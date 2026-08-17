from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RelatedNote:
    path: str
    title: str
    score: int
    matched_terms: list[str]
    excerpt: str


def load_user_settings(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_search_terms(request: dict[str, Any]) -> list[str]:
    raw_terms: list[str] = []
    raw_terms.extend(split_terms(request.get("title", "")))
    raw_terms.extend(split_terms(request.get("objective", "")))
    raw_terms.extend(split_terms(request.get("related_project", "")))
    for item in request.get("scope", []):
        raw_terms.extend(split_terms(str(item)))
    for tag in request.get("tags", []):
        raw_terms.extend(split_terms(str(tag).replace("-", " ")))

    seen: set[str] = set()
    terms: list[str] = []
    for term in raw_terms:
        normalized = term.strip().lower()
        if len(normalized) < 2 or normalized in seen:
            continue
        seen.add(normalized)
        terms.append(normalized)
    return terms


def filter_search_terms(terms: list[str], ignored_terms: list[str] | None = None) -> list[str]:
    ignored = {term.lower() for term in ignored_terms or []}
    return [term for term in terms if term.lower() not in ignored]


def split_terms(value: str) -> list[str]:
    if not value:
        return []
    ascii_terms = re.findall(r"[A-Za-z0-9]{2,}", value)
    non_ascii_terms = re.findall(r"[\u3040-\u30ff\u3400-\u9fff\U0001f300-\U0001ffff]{2,}", value)
    return ascii_terms + non_ascii_terms


def find_related_notes(
    vault_path: Path,
    request: dict[str, Any],
    max_notes: int = 10,
    max_excerpt_chars: int = 500,
    exclude_folders: list[str] | None = None,
    ignored_terms: list[str] | None = None,
    min_score: int = 1,
) -> list[RelatedNote]:
    try:
        if not vault_path.exists():
            return []
    except OSError:
        return []

    terms = filter_search_terms(build_search_terms(request), ignored_terms)
    excluded = set(exclude_folders or [])
    candidates: list[RelatedNote] = []

    for note_path in iter_markdown_notes(vault_path, excluded):
        try:
            text = note_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        score, matched_terms = score_note(note_path, text, terms)
        if score < min_score:
            continue

        candidates.append(
            RelatedNote(
                path=str(note_path),
                title=note_path.stem,
                score=score,
                matched_terms=matched_terms,
                excerpt=make_excerpt(text, matched_terms, max_excerpt_chars),
            )
        )

    candidates.sort(key=lambda note: (-note.score, note.title))
    return candidates[:max_notes]


def iter_markdown_notes(vault_path: Path, exclude_folders: set[str]):
    for path in vault_path.rglob("*.md"):
        parts = set(path.relative_to(vault_path).parts)
        if parts.intersection(exclude_folders):
            continue
        yield path


def score_note(path: Path, text: str, terms: list[str]) -> tuple[int, list[str]]:
    haystack_title = path.stem.lower()
    haystack_text = text.lower()
    matched: list[str] = []
    score = 0
    for term in terms:
        title_hits = haystack_title.count(term)
        text_hits = haystack_text.count(term)
        if title_hits or text_hits:
            matched.append(term)
            score += title_hits * 5 + min(text_hits, 5)
    return score, matched


def make_excerpt(text: str, matched_terms: list[str], max_chars: int) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return ""
    lower = compact.lower()
    positions = [lower.find(term) for term in matched_terms if lower.find(term) >= 0]
    start = max(min(positions) - 80, 0) if positions else 0
    excerpt = compact[start : start + max_chars]
    return excerpt.strip()


def summarize_related_notes(notes: list[RelatedNote]) -> dict[str, Any]:
    return {
        "related_note_count": len(notes),
        "notes": [
            {
                "path": note.path,
                "title": note.title,
                "score": note.score,
                "matched_terms": note.matched_terms,
                "excerpt": note.excerpt,
            }
            for note in notes
        ],
    }
