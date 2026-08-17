from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from .pipeline import PipelineResult
except ImportError:
    from pipeline import PipelineResult


DEFAULT_MOBILE_REVIEW_FOLDER = "99_Mobile_Review"

NOTE_ORDER = {
    "10_Daily_Intelligence": "01_daily_intelligence",
    "00_Inbox": "02_review_queue",
    "30_Strategic_Intelligence": "03_strategic_intelligence",
    "50_Hypotheses": "04_hypothesis",
    "60_Decisions": "05_decision",
    "70_Actions_and_Results": "06_result",
    "90_Sources": "07_source_digest",
}


def mobile_review_enabled(settings: dict[str, Any]) -> bool:
    options = settings.get("mobile_review_copy", {})
    if options is False:
        return False
    if isinstance(options, dict):
        return bool(options.get("enabled", True))
    return True


def mobile_review_folder_name(settings: dict[str, Any]) -> str:
    options = settings.get("mobile_review_copy", {})
    if isinstance(options, dict):
        folder = str(options.get("folder", DEFAULT_MOBILE_REVIEW_FOLDER)).strip()
        if folder:
            return folder
    return DEFAULT_MOBILE_REVIEW_FOLDER


def write_mobile_review_copies(
    output_root: Path,
    pipeline_result: PipelineResult,
    settings: dict[str, Any],
    title: str,
) -> list[Path]:
    if not mobile_review_enabled(settings):
        return []

    mobile_root = output_root / mobile_review_folder_name(settings)
    run_mobile_root = mobile_root / pipeline_result.run_id
    run_mobile_root.mkdir(parents=True, exist_ok=True)

    files: list[Path] = []
    ordered_notes = sorted(pipeline_result.created_notes, key=mobile_sort_key)
    index_path = run_mobile_root / "00_index.txt"
    index_path.write_text(render_index(title, pipeline_result.run_id, ordered_notes), encoding="utf-8")
    files.append(index_path)

    latest_candidate: Path | None = None
    for note in ordered_notes:
        target = run_mobile_root / f"{mobile_filename(note)}.txt"
        target.write_text(note.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
        files.append(target)
        if latest_candidate is None and note.parent.name in {"10_Daily_Intelligence", "30_Strategic_Intelligence"}:
            latest_candidate = target

    latest_source = latest_candidate or (files[1] if len(files) > 1 else index_path)
    latest_path = mobile_root / "latest_review.txt"
    latest_path.write_text(latest_source.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    files.append(latest_path)

    latest_index_path = mobile_root / "latest_index.txt"
    latest_index_path.write_text(index_path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    files.append(latest_index_path)
    return files


def mobile_sort_key(path: Path) -> tuple[int, str]:
    key = NOTE_ORDER.get(path.parent.name, "99_other")
    return int(key.split("_", 1)[0]), path.name


def mobile_filename(path: Path) -> str:
    return NOTE_ORDER.get(path.parent.name, f"99_{path.parent.name.lower()}")


def render_index(title: str, run_id: str, notes: list[Path]) -> str:
    lines = [
        f"AI Intelligence Unit Mobile Review",
        f"Title: {title}",
        f"Run ID: {run_id}",
        "",
        "Files",
    ]
    for note in sorted(notes, key=mobile_sort_key):
        lines.append(f"- {mobile_filename(note)}.txt : {note.name}")
    lines.extend(
        [
            "",
            "Open the .txt files from Google Drive on mobile.",
            "The .md files remain the Obsidian source files.",
        ]
    )
    return "\n".join(lines) + "\n"
