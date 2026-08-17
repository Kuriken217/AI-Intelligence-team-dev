from __future__ import annotations

from datetime import datetime
from pathlib import Path


ALLOWED_REVIEW_STATUSES = {"approved", "rejected", "watchlist", "user_review"}
ALLOWED_SYSTEM_STATUSES = ALLOWED_REVIEW_STATUSES | {"decided", "completed"}


def append_review(note_path: Path, status: str, comment: str, now: datetime | None = None) -> None:
    if status not in ALLOWED_REVIEW_STATUSES:
        raise ValueError(f"Unsupported review status: {status}")

    now = now or datetime.now()
    update_note_status(note_path, status, now)
    append_section_entry(
        note_path,
        "User Review Log",
        [
            f"- Date: {now:%Y-%m-%d}",
            f"- Status: {status}",
            f"- Comment: {comment}",
        ],
    )


def append_decision(note_path: Path, decision: str, reason: str, now: datetime | None = None) -> None:
    now = now or datetime.now()
    update_note_status(note_path, "decided", now)
    append_section_entry(
        note_path,
        "Decision Log",
        [
            f"- Date: {now:%Y-%m-%d}",
            f"- Decision: {decision}",
            f"- Reason: {reason}",
        ],
    )


def append_result(note_path: Path, action: str, result: str, feedback: str, now: datetime | None = None) -> None:
    now = now or datetime.now()
    update_note_status(note_path, "completed", now)
    append_section_entry(
        note_path,
        "Result Log",
        [
            f"- Date: {now:%Y-%m-%d}",
            f"- Action: {action}",
            f"- Result: {result}",
            f"- Feedback: {feedback}",
        ],
    )


def update_note_status(note_path: Path, status: str, now: datetime | None = None) -> None:
    if status not in ALLOWED_SYSTEM_STATUSES:
        raise ValueError(f"Unsupported status: {status}")

    now = now or datetime.now()
    text = note_path.read_text(encoding="utf-8")
    updated = replace_frontmatter_field(text, "status", status)
    updated = replace_frontmatter_field(updated, "updated", f"{now:%Y-%m-%d}")
    note_path.write_text(updated, encoding="utf-8")


def replace_frontmatter_field(text: str, field: str, value: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        return text

    prefix = f"{field}:"
    for index in range(1, end_index):
        if lines[index].startswith(prefix):
            lines[index] = f"{field}: {value}"
            return "\n".join(lines) + "\n"

    lines.insert(end_index, f"{field}: {value}")
    return "\n".join(lines) + "\n"


def append_section_entry(note_path: Path, heading: str, lines: list[str]) -> None:
    text = note_path.read_text(encoding="utf-8").rstrip()
    entry = "\n".join(lines)
    if f"## {heading}" not in text:
        text = f"{text}\n\n## {heading}\n\n{entry}\n"
    else:
        text = f"{text}\n\n{entry}\n"
    note_path.write_text(text, encoding="utf-8")

