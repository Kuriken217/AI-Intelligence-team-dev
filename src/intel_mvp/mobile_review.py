from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    from .pipeline import PipelineResult
except ImportError:
    from pipeline import PipelineResult


DEFAULT_MOBILE_FOLDER_NAME = "For Mobile"


def mobile_review_enabled(settings: dict[str, Any]) -> bool:
    options = settings.get("mobile_review_copy", {})
    if options is False:
        return False
    if isinstance(options, dict):
        return bool(options.get("enabled", True))
    return True


def mobile_folder_name(settings: dict[str, Any]) -> str:
    options = settings.get("mobile_review_copy", {})
    if isinstance(options, dict):
        configured = str(options.get("folder_name", options.get("folder", DEFAULT_MOBILE_FOLDER_NAME))).strip()
        if configured and configured != "99_Mobile_Review":
            return configured
    return DEFAULT_MOBILE_FOLDER_NAME


def write_mobile_review_copies(
    output_root: Path,
    pipeline_result: PipelineResult,
    settings: dict[str, Any],
    title: str,
) -> list[Path]:
    if not mobile_review_enabled(settings):
        return []

    folder_name = mobile_folder_name(settings)
    files: list[Path] = []
    for note in pipeline_result.created_notes:
        target_dir = note.parent / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{note.stem}.txt"
        mobile_text = render_mobile_text(note, title, pipeline_result.run_id, output_root)
        target_path.write_text(mobile_text, encoding="utf-8")
        files.append(target_path)

        latest_path = target_dir / "latest.txt"
        latest_path.write_text(mobile_text, encoding="utf-8")
        files.append(latest_path)

    return files


def render_mobile_text(note_path: Path, title: str, run_id: str, output_root: Path) -> str:
    raw_text = note_path.read_text(encoding="utf-8", errors="ignore")
    body = markdown_to_mobile_text(strip_frontmatter(raw_text))
    relative_note = note_path.relative_to(output_root) if output_root in note_path.parents else note_path
    header = [
        "AI Intelligence Unit",
        f"Title: {title}",
        f"Run ID: {run_id}",
        f"Original Obsidian note: {relative_note}",
        "",
    ]
    return "\n".join(header) + body.strip() + "\n"


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            return text[end + len("\n---\n") :]
    return text


def markdown_to_mobile_text(text: str) -> str:
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1\n  URL: \2", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"
