from __future__ import annotations

from typing import Any

try:
    from .source_quality import source_quality_gaps
except ImportError:
    from source_quality import source_quality_gaps


def build_mission_brief(
    request: dict[str, Any],
    run_id: str,
    prior_knowledge_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "title": request["title"],
        "objective": request["objective"],
        "decision_context": request["decision_context"],
        "scope": request["scope"],
        "success_criteria": [
            "Decision context is directly addressed.",
            "Sources remain traceable.",
            "Facts, interpretations, hypotheses, and recommendations are separated.",
            "Red Team objections are included before strategic recommendation.",
            "Obsidian notes are ready for user review and later feedback.",
        ],
        "agent_tasks": {
            "collector": ["Collect relevant sources and preserve traceability."],
            "analyst": ["Separate facts from interpretation and identify uncertainty."],
            "editor": ["Integrate findings into a decision-oriented brief."],
            "red_team": ["Challenge evidence, assumptions, and confidence."],
            "strategist": ["Convert intelligence into decision options and actions."],
            "knowledge_keeper": ["Save the run as linked Obsidian notes."],
        },
        "prior_knowledge_summary": prior_knowledge_summary or {"related_note_count": 0, "notes": []},
    }


def build_source_digest(sources: list[dict[str, str]]) -> dict[str, Any]:
    source_gaps = source_quality_gaps(sources)
    if not source_gaps:
        source_gaps = ["No immediate source quality gaps detected in the current source set."]

    return {
        "sources": sources,
        "fact_candidates": [source.get("summary", "") for source in sources if source.get("summary")],
        "collection_gaps": source_gaps,
    }


def build_analysis_packet(source_digest: dict[str, Any]) -> dict[str, Any]:
    fact_candidates = source_digest["fact_candidates"]
    return {
        "facts": fact_candidates,
        "interpretations": [
            "The source set should be treated as current situational intelligence until the next official update is available.",
            "Observed indicators and forecast indicators should be kept separate because they carry different uncertainty profiles.",
        ],
        "insights": [
            "The most useful signal is the direction shared across independent public agencies, not any single headline.",
            "Decision value improves when source dates, baselines, and geographic scope are preserved with each claim.",
        ],
        "hypotheses": [
            "If multiple official indicators continue to move in the same direction, the topic should remain an active intelligence watch item."
        ],
        "uncertainties": [
            "The source set may mix monthly observations, model-based forecasts, and broader background datasets.",
            "Regional impacts may diverge from the global signal.",
            "Newer official releases may change rankings, anomalies, or near-term outlooks.",
        ],
    }


def build_integrated_intelligence(analysis_packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": "The theme is relevant for monitoring, but conclusions should remain tied to official source dates and uncertainty.",
        "key_findings": analysis_packet["insights"],
        "implications": [
            "The topic can support a short intelligence brief or news update now.",
            "The next research step should compare follow-up official releases and track whether the signal persists.",
        ],
        "confidence": {
            "level": "medium",
            "rationale": "The sources are traceable and official, but the brief still depends on a limited source set and current publication timing.",
        },
        "open_questions": analysis_packet["uncertainties"],
    }


def build_red_team_review(integrated_intelligence: dict[str, Any]) -> dict[str, Any]:
    return {
        "counterpoints": [
            "Monthly records can be attention-grabbing but may not describe every region or impact category.",
            "Forecast products should not be presented as observed outcomes.",
        ],
        "bias_risks": [
            "Recent extreme indicators may make the overall trend feel more certain than the evidence permits.",
            "Source selection may overweight English-language global agencies and underweight regional agencies.",
        ],
        "missing_information": integrated_intelligence["open_questions"],
        "confidence_adjustments": [
            "Keep confidence at medium until additional official updates or regional corroboration are added."
        ],
        "must_verify": [
            "Publication date and latest-release status",
            "Baseline period used for anomalies",
            "Observed indicator versus forecast indicator",
            "Regional exceptions and impact evidence",
        ],
    }


def build_strategy_packet(red_team_review: dict[str, Any]) -> dict[str, Any]:
    return {
        "recommendation": "Publish as a monitored intelligence brief, while clearly separating verified observations from outlook-based risk signals.",
        "options": [
            "Approve as active intelligence theme",
            "Keep in watchlist pending the next official update",
            "Defer if the source set is too narrow for the intended audience",
        ],
        "next_actions": [
            "Add the next NOAA/NASA/Copernicus/WMO update when released.",
            "Separate global indicators from regional impact notes.",
            "Create a recurring watch item for anomalies, sea surface temperatures, ENSO, and sea ice.",
        ],
        "watch_items": red_team_review["must_verify"],
        "decision_prompt": "Should this topic become an active intelligence theme for the related project?",
    }


def build_knowledge_keeper_packet(created_notes: list[str]) -> dict[str, Any]:
    return {
        "notes": created_notes,
        "review_queue": [
            "Strategic Intelligence Report",
            "Decision Note",
            "Result Note",
        ],
    }
