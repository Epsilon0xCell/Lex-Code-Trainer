#!/usr/bin/env python3
"""Lex - the AI programming assistant done right.

Lex never dumps a wall of code on you. It reveals a program ONE line at a
time, and the next line only unlocks after you explain - in your own words -
what the line you just saw actually does. Lex checks your explanation
against the key concepts for that line, so you cannot copy-paste your way
through: you have to understand each line.

Usage:
    python3 lex.py                  # list built-in lessons
    python3 lex.py --lesson loops   # study a built-in lesson
    python3 lex.py --file code.py   # line-by-line mode for your own file
                                    # (explanations recorded, not graded)
"""
import argparse
import re
import sys

# Each lesson: (title, [(code_line, [key concepts]), ...])
# I store each lesson as the lines of one small finished program
# plus the words a real explanation of that line should contain.
# Those concept lists are the whole grading standard. There is no
# model behind the grading, just these words.
# The blank line inside the functions lesson is a lesson line too.
# It carries no concepts, so run_lesson shows it and moves on
# without asking for an explanation.
LESSONS = {
    "functions": (
        "Defining and calling a function (Python)",
        [
            ("def greet(name):", ["define", "function", "parameter", "name"]),
            ('    message = f"Hello, {name}!"', ["assign", "variable", "f-string", "string"]),
            ("    return message", ["return", "value", "back"]),
            ("", []),
            ('print(greet("world"))', ["call", "print", "argument"]),
        ],
    ),
    "loops": (
        "Looping over a list (Python)",
        [
            ("total = 0", ["initial", "variable", "zero", "start"]),
            ("for number in [1, 2, 3]:", ["loop", "iterate", "each", "list"]),
            ("    total += number", ["add", "accumul", "sum", "increase"]),
            ("print(total)", ["print", "output", "result"]),
        ],
    ),
    "api": (
        "Making an HTTP request (Python)",
        [
            ("import urllib.request", ["import", "library", "module"]),
            ('url = "https://api.github.com"', ["variable", "url", "address", "string"]),
            ("with urllib.request.urlopen(url) as response:", ["open", "request", "connection", "context"]),
            ("    data = response.read()", ["read", "response", "data", "body"]),
            ("print(len(data))", ["print", "length", "size"]),
        ],
    ),
}
PASS_MARK = 0.5  # fraction of key concepts an explanation must mention


def grade(explanation, concepts):
    # A line with no concepts has nothing to miss, so I return a
    # full score instead of dividing by zero on the return line
    # below. run_lesson skips those lines before it ever calls
    # this function, so the guard is for any other caller.
    if not concepts:
        return 1.0, []
    # I compare word sets, so the order of an explanation and any
    # words repeated in it count for nothing. Only which concept
    # stems show up at all decides the score.
    words = set(re.findall(r"[a-z]+", explanation.lower()))

    def mentioned(concept):
        # Split hyphenated concepts such as "f-string" into word parts: a
        # single stem built from the raw concept ("f-str") can never match
        # any word in an explanation, because explanation words contain no
        # hyphens.
        parts = re.findall(r"[a-z]+", concept.lower())
        return any(w == part or w.startswith(part[:5]) for part in parts for w in words)

    hits = [c for c in concepts if mentioned(c)]
    # The stem match is loose at the short end. A one letter part
    # such as the "f" in "f-string" is matched by any word that
    # starts with that letter, so that concept can be earned by an
    # explanation that never names it. The looseness gives credit
    # too easily. It never withholds credit from an explanation
    # that does name the concept, which is the direction I care
    # about more.
    return len(hits) / len(concepts), [c for c in concepts if c not in hits]


def run_lesson(title, lines):
    print(f"\n=== Lex lesson: {title} ===")
    print("Explain each line to unlock the next. Type 'skip' to reveal anyway.\n")
    score, graded = 0.0, 0
    # I show the line first and grade the explanation before the
    # next line appears. A low grade never holds the lesson up.
    # The line after still comes, and the miss is recorded only
    # in the final score.
    for i, (line, concepts) in enumerate(lines, 1):
        print(f"Line {i}: {line if line else '(blank line)'}")
        if not concepts:
            continue
        try:
            answer = input("  Your explanation: ").strip()
        except EOFError:
            # Closing the input ends the lesson where it stands.
            # Lines already graded still count, so the score
            # printed after the loop is over the lines reached,
            # not over the whole lesson.
            print()
            break
        if answer.lower() == "skip":
            print("  Skipped - but skipping is how bugs are born.")
            # I count a skip as a graded line with no credit. If
            # skips stayed out of the count, skipping every line
            # would leave no score at all instead of a zero.
            graded += 1
            continue
        ratio, missed = grade(answer, concepts)
        graded += 1
        score += ratio
        if ratio >= PASS_MARK:
            print(f"  Lex: correct enough ({ratio:.0%}). Next line unlocked.")
        else:
            print(f"  Lex: not quite ({ratio:.0%}). You missed: {', '.join(missed)}.")
            print("  The line is revealed anyway - re-read it until it clicks.")
    if graded:
        print(f"\nLesson complete. Understanding score: {score / graded:.0%}")
    return 0


def run_file(path):
    try:
        # errors="replace" is a choice, not a default I fell into.
        # A file with bytes this UTF-8 read cannot decode should
        # still open line by line instead of failing before the
        # first line shows.
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError as exc:
        print(f"Lex: cannot open {path}: {exc.strerror or exc}", file=sys.stderr)
        return 1
    print(f"\n=== Lex file mode: {path} ({len(lines)} lines) ===")
    print("One line at a time. Explain it to reveal the next.\n")
    # I track completion in its own flag because the two end
    # messages make different claims. Reaching the last line of
    # the file is the only path that earns the complete message.
    completed = True
    for i, line in enumerate(lines, 1):
        print(f"{i:>4}: {line}")
        # Blank lines print for shape but are never prompted on.
        # There is nothing to explain in an empty line, and
        # stopping for one would break the rhythm of reading.
        if line.strip():
            try:
                input("  Your explanation (Enter to continue): ")
            except EOFError:
                print()
                completed = False
                break
    if completed:
        print("\nFile complete. If you explained every line out loud, you own this code now.")
    else:
        print("File abandoned before the end. The lines after the break still wait for you.")
    return 0


def main(argv=None):
    # The lesson names offered in --help come from LESSONS itself
    # through the choices list below, so an unknown name is
    # refused by argparse before any lesson code runs.
    parser = argparse.ArgumentParser(description="Lex - learn code one line at a time.")
    parser.add_argument("--lesson", choices=sorted(LESSONS), help="built-in lesson to study")
    parser.add_argument("--file", help="study your own file line by line")
    args = parser.parse_args(argv)
    # File mode is checked first, so it wins when both flags are
    # given. If I pass my own file and a lesson name together by
    # mistake, my file is the one I meant.
    if args.file:
        return run_file(args.file)
    if args.lesson:
        title, lines = LESSONS[args.lesson]
        return run_lesson(title, lines)
    print("Lex - the AI programming assistant done right.\n")
    print("Built-in lessons:")
    for key, (title, lines) in LESSONS.items():
        print(f"  {key:<10} {title} ({len(lines)} lines)")
    print("\nRun: python3 lex.py --lesson loops")
    print("Or:  python3 lex.py --file your_code.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
