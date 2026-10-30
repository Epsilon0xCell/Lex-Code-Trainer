![Lex banner](banner.png)

# Lex-Code-Trainer

Lex is the AI programming assistant done right.

# What makes Lex-Code-Trainer different?

Lex ensures that you are not copying and pasting code but rather
understanding each line. After Lex shows you code, only a single line is
revealed at a time, and you are asked to explain in technical detail what
that line is doing to reveal the next.

## Implementation

This project is complete and runnable, with no dependencies beyond the
Python 3 standard library. Run it:

```bash
python3 lex.py                  # list lessons
python3 lex.py --lesson loops   # study a lesson
python3 lex.py --file code.py   # line-by-line mode for your own code
```

There are three built-in lessons: `functions`, `loops`, and `api`.
In a lesson, each line is graded against its key concepts: your
explanation needs to mention at least half of them (stem matching, so
`accumulate` covers `accumul`) to be counted as correct enough. Typing
`skip` reveals the next line without credit. At the end, Lex prints your
understanding score as a percentage of the graded lines. Blank lines are
shown but not graded.

In `--file` mode your explanations are not graded: Lex shows each
non-blank line of your file and waits for you to type an explanation or
press Enter before revealing the next line.

## Behaviour verified by testing

- `python3 lex.py` lists the three lessons and exits 0.
  `--lesson` with an unknown name is rejected by argparse with exit 2.
- A fully correct run through the `functions` lesson scores 100 percent,
  including the f-string line: the concept `f-string` is matched by its
  word parts, so an explanation mentioning an f-string can earn that
  concept.
- Closing the input (EOF) during a lesson stops the lesson without a
  score and without a traceback, exit 0.
- `--file` with a missing path or a directory prints a short
  `Lex: cannot open ...` message to stderr and exits 1, with no traceback.
- Closing the input part-way through `--file` mode ends with
  `File abandoned before the end.` instead of claiming the file was
  completed. A file read to the end ends with the `File complete.`
  message. An empty file completes immediately.
- If both `--file` and `--lesson` are given, `--file` takes precedence.

## Files

- `lex.py` - the whole program, lessons included
- `LICENSE` - MIT License
