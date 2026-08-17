from __future__ import annotations

from typing import Any


def build_prior_knowledge_delta(
    prior_knowledge_summary: dict[str, Any],
    source_digest: dict[str, Any],
) -> dict[str, Any]:
    prior_text = " ".join(note.get("excerpt", "") for note in prior_knowledge_summary.get("notes", [])).lower()
    fact_candidates = source_digest.get("fact_candidates", [])

    new_fact_candidates = []
    already_seen_candidates = []
    for fact in fact_candidates:
        normalized = str(fact).strip()
        if not normalized:
            continue
        if normalized.lower() in prior_text:
            already_seen_candidates.append(normalized)
        else:
            new_fact_candidates.append(normalized)

    return {
        "prior_note_count": prior_knowledge_summary.get("related_note_count", 0),
        "new_fact_candidates": new_fact_candidates,
        "already_seen_candidates": already_seen_candidates,
        "delta_summary": summarize_delta(prior_knowledge_summary, new_fact_candidates),
    }


def summarize_delta(prior_knowledge_summary: dict[str, Any], new_fact_candidates: list[str]) -> str:
    prior_count = prior_knowledge_summary.get("related_note_count", 0)
    if prior_count == 0:
        return "No related prior notes were available, so all current fact candidates should be treated as new to this run."
    if not new_fact_candidates:
        return "Current fact candidates appear to overlap with prior note excerpts. Review may focus on confirmation and confidence changes."
    return "Some current fact candidates do not appear in prior note excerpts and should be reviewed as potential knowledge updates."

