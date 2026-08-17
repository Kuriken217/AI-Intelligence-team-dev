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
    source_gaps = source_quality_gaps(sources) + [
        "Customer adoption evidence is not yet verified.",
    ]

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
            "Rising AI rack density may increase pressure on data center cooling architecture.",
            "Supplier expansion may indicate expected demand, but announcements alone are not proof of durable adoption.",
        ],
        "insights": [
            "Cooling constraints can become a bottleneck for AI infrastructure scaling.",
            "The most useful research angle is supplier exposure plus customer validation.",
        ],
        "hypotheses": [
            "AI data center power density may create sustained demand for liquid cooling infrastructure and related suppliers."
        ],
        "uncertainties": [
            "Adoption rates are not yet validated.",
            "Retrofit economics and maintenance risks remain unclear.",
            "Competitive differentiation among suppliers is not yet established.",
        ],
    }


def build_integrated_intelligence(analysis_packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": "The theme is strategically relevant but still needs primary-source validation before strong action.",
        "key_findings": analysis_packet["insights"],
        "implications": [
            "The topic should remain active if the user tracks AI infrastructure opportunities.",
            "The next research step should focus on direct beneficiaries and deployment evidence.",
        ],
        "confidence": {
            "level": "medium",
            "rationale": "The direction is plausible, but current evidence is not yet deep enough for a high-confidence conclusion.",
        },
        "open_questions": analysis_packet["uncertainties"],
    }


def build_red_team_review(integrated_intelligence: dict[str, Any]) -> dict[str, Any]:
    return {
        "counterpoints": [
            "Supplier announcements may overstate actual customer adoption.",
            "Thermal constraints may be solved by broader facility redesign rather than narrow liquid-cooling suppliers.",
        ],
        "bias_risks": [
            "AI infrastructure enthusiasm may inflate perceived certainty.",
            "Source selection may overweight recent market narratives.",
        ],
        "missing_information": integrated_intelligence["open_questions"],
        "confidence_adjustments": [
            "Keep overall confidence at medium until primary sources and deployment data are added."
        ],
        "must_verify": [
            "Customer adoption evidence",
            "Revenue contribution",
            "Reliability and maintenance record",
            "Supplier differentiation",
        ],
    }


def build_strategy_packet(red_team_review: dict[str, Any]) -> dict[str, Any]:
    return {
        "recommendation": "Keep this as a high-priority watch theme, but do not convert it into a firm thesis until verification items are addressed.",
        "options": [
            "Approve as active intelligence theme",
            "Keep in watchlist pending primary-source validation",
            "Defer until deployment evidence improves",
        ],
        "next_actions": [
            "Add primary sources.",
            "Build a supplier exposure map.",
            "Track customer deployments and reliability signals.",
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
