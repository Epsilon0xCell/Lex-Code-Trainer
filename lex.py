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
    if not concepts:
        return 1.0, []
    words = set(re.findall(r"[a-z]+", explanation.lower()))

    def mentioned(concept):
        stem = concept.lower()[:5]
        return any(w.startswith(stem) for w in words)

    hits = [c for c in concepts if mentioned(c)]
    return len(hits) / len(concepts), [c for c in concepts if c not in hits]


def run_lesson(title, lines):
    print(f"\n=== Lex lesson: {title} ===")
    print("Explain each line to unlock the next. Type 'skip' to reveal anyway.\n")
    score, graded = 0.0, 0
    for i, (line, concepts) in enumerate(lines, 1):
        print(f"Line {i}: {line if line else '(blank line)'}")
        if not concepts:
            continue
        try:
            answer = input("  Your explanation: ").strip()
        except EOFError:
            print()
            break
        if answer.lower() == "skip":
            print("  Skipped - but skipping is how bugs are born.")
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
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    print(f"\n=== Lex file mode: {path} ({len(lines)} lines) ===")
    print("One line at a time. Explain it to reveal the next.\n")
    for i, line in enumerate(lines, 1):
        print(f"{i:>4}: {line}")
        if line.strip():
            try:
                input("  Your explanation (Enter to continue): ")
            except EOFError:
                print()
                break
    print("\nFile complete. If you explained every line out loud, you own this code now.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lex - learn code one line at a time.")
    parser.add_argument("--lesson", choices=sorted(LESSONS), help="built-in lesson to study")
    parser.add_argument("--file", help="study your own file line by line")
    args = parser.parse_args(argv)
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
