"""
Generate interview answer markdown files from QUESTIONS.txt.

Creates docs/interview_answers/Q01.md ... Q57.md with the question
and a placeholder section to be filled with a 600+ word answer.

Run with: python scripts/generate_interview_docs.py
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_FILE = ROOT / "QUESTIONS.txt"
OUT_DIR = ROOT / "docs" / "interview_answers"


def read_questions() -> list[str]:
    if not QUESTIONS_FILE.exists():
        raise FileNotFoundError(f"QUESTIONS.txt not found at {QUESTIONS_FILE}")
    lines = QUESTIONS_FILE.read_text(encoding="utf-8").splitlines()
    # Extract numbered questions: lines that end with '?' and are indented in the source
    # We'll include all non-empty lines that are not section headers.
    questions: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Skip obvious section headers
        if stripped.endswith(":") or stripped.lower().endswith("design and scaling"):
            continue
        # Heuristic: consider lines that end with '?' as questions
        if stripped.endswith("?"):
            questions.append(stripped)
    return questions


def ensure_output_dir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def write_markdown(idx: int, question: str) -> None:
    filename = f"Q{idx:02d}.md"
    path = OUT_DIR / filename
    if path.exists():
        return
    template = f"""---
title: Interview Question {idx:02d}
question_number: {idx}
---

# Q{idx:02d}. {question}

Answer (at least 600 words):

"""
    path.write_text(template, encoding="utf-8")


def main() -> None:
    questions = read_questions()
    if len(questions) < 57:
        # If fewer than 57 were parsed, we still create placeholders up to 57
        # The user can paste the remaining questions later.
        pass

    ensure_output_dir()
    for i in range(1, 58):
        q = questions[i - 1] if i - 1 < len(questions) else f"Question {i} (placeholder)"
        write_markdown(i, q)

    print(f"Wrote placeholders to {OUT_DIR}.")


if __name__ == "__main__":
    main()


