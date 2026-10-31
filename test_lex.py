"""Tests for lex.py: grading, lesson runs, and file mode."""
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

from lex import grade, run_file, run_lesson, LESSONS  # noqa: E402


def run_program(args, stdin_text):
    return subprocess.run(
        [sys.executable, str(HERE / "lex.py")] + args,
        input=stdin_text, capture_output=True, text=True, timeout=15,
    )


class GradeTests(unittest.TestCase):
    def test_no_concepts_scores_full(self):
        self.assertEqual(grade("anything at all", []), (1.0, []))

    def test_empty_explanation_scores_zero(self):
        ratio, missed = grade("", ["define", "function"])
        self.assertEqual(ratio, 0.0)
        self.assertEqual(missed, ["define", "function"])

    def test_stem_matching_still_works(self):
        self.assertEqual(grade("accumulate the total", ["accumul"])[0], 1.0)
        self.assertEqual(grade("it prints the output", ["print"])[0], 1.0)

    def test_f_string_false_positive_is_fixed(self):
        # Pinned regression: this explanation never names an
        # f-string, but its f-words used to earn the concept
        # because the one letter part "f" matched by prefix.
        ratio, missed = grade(
            "this function formats a value for printing", ["f-string"]
        )
        self.assertEqual(ratio, 0.0)
        self.assertEqual(missed, ["f-string"])

    def test_f_string_earns_when_named(self):
        self.assertEqual(
            grade("assign a variable using an f-string", ["f-string"])[0], 1.0
        )
        self.assertEqual(grade("an f string literal", ["f-string"])[0], 1.0)
        self.assertEqual(grade("an fstring literal", ["f-string"])[0], 1.0)

    def test_partial_credit_counts_concepts(self):
        ratio, missed = grade("define a thing", ["define", "function"])
        self.assertEqual(ratio, 0.5)
        self.assertEqual(missed, ["function"])


class LessonRunTests(unittest.TestCase):
    CORRECT = (
        "define a function with a parameter name\n"
        "assign a variable with an f-string string\n"
        "return the value back\n"
        "call print with an argument\n"
    )

    def test_functions_lesson_full_marks(self):
        r = run_program(["--lesson", "functions"], self.CORRECT)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Understanding score: 100%", r.stdout)

    def test_skip_everything_scores_zero(self):
        r = run_program(["--lesson", "functions"], "skip\nskip\nskip\nskip\n")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Understanding score: 0%", r.stdout)

    def test_eof_mid_lesson_scores_lines_reached(self):
        # "set a variable to zero to start" names 3 of the 4
        # concepts on line 1 (variable, zero, start), so the
        # score over the one line reached is 75%.
        r = run_program(["--lesson", "loops"], "set a variable to zero to start\n")
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("Understanding score: 75%", r.stdout)

    def test_eof_at_first_line_prints_no_score(self):
        r = run_program(["--lesson", "loops"], "")
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("Understanding score", r.stdout)

    def test_keyboard_interrupt_ends_lesson_without_traceback(self):
        title, lines = LESSONS["loops"]
        with mock.patch("builtins.input", side_effect=KeyboardInterrupt):
            with mock.patch("sys.stdout"):
                self.assertEqual(run_lesson(title, lines), 0)

    def test_lesson_list_and_help(self):
        r = run_program([], "")
        self.assertEqual(r.returncode, 0)
        for name in ("functions", "loops", "api"):
            self.assertIn(name, r.stdout)
        r = run_program(["--help"], "")
        self.assertEqual(r.returncode, 0)

    def test_unknown_lesson_rejected_by_argparse(self):
        r = run_program(["--lesson", "nope"], "")
        self.assertEqual(r.returncode, 2)


class FileModeTests(unittest.TestCase):
    def test_missing_file_exits_one(self):
        r = run_program(["--file", "/nope/missing.py"], "")
        self.assertEqual(r.returncode, 1)
        self.assertIn("cannot open", r.stderr)

    def test_directory_exits_one(self):
        r = run_program(["--file", "/tmp"], "")
        self.assertEqual(r.returncode, 1)

    def test_empty_file_completes(self):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".py", delete=False, dir="/tmp"
        ) as fh:
            path = fh.name
        r = run_program(["--file", path], "")
        self.assertEqual(r.returncode, 0)
        self.assertIn("File complete.", r.stdout)

    def test_file_read_to_end_completes(self):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".py", delete=False, dir="/tmp"
        ) as fh:
            fh.write("x = 1\n\ny = 2\n")
            path = fh.name
        r = run_program(["--file", path], "assigns one\nadds two\n")
        self.assertEqual(r.returncode, 0)
        self.assertIn("File complete.", r.stdout)

    def test_file_abandoned_on_short_input(self):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".py", delete=False, dir="/tmp"
        ) as fh:
            fh.write("x = 1\ny = 2\n")
            path = fh.name
        r = run_program(["--file", path], "only one line of input\n")
        self.assertEqual(r.returncode, 0)
        self.assertIn("File abandoned before the end.", r.stdout)

    def test_keyboard_interrupt_in_file_mode_abandons(self):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".py", delete=False, dir="/tmp"
        ) as fh:
            fh.write("x = 1\n")
            path = fh.name
        with mock.patch("builtins.input", side_effect=KeyboardInterrupt):
            with mock.patch("sys.stdout"):
                self.assertEqual(run_file(path), 0)

    def test_file_flag_wins_over_lesson(self):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".py", delete=False, dir="/tmp"
        ) as fh:
            path = fh.name
        r = run_program(["--file", path, "--lesson", "loops"], "")
        self.assertIn("file mode", r.stdout)
