from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class NewsBrief:
    headline: str
    lead: str
    key_developments: list[str]
    why_it_matters: list[str]
    potential_implications: list[str]
    confidence: str
    uncertainty: list[str]
    watch_next: list[str]
    red_team_checks: list[str]
    source_links: list[str]


def build_news_brief(request: dict[str, Any], sources: list[dict[str, str]], now: datetime) -> NewsBrief:
    options = request.get("news_brief", {})
    if not isinstance(options, dict):
        options = {}

    source_summaries = [source.get("summary", "").strip() for source in sources if source.get("summary", "").strip()]
    headline = str(options.get("headline") or default_headline(request, sources)).strip()
    lead = str(options.get("lead") or (source_summaries[0] if source_summaries else request.get("objective", ""))).strip()
    key_developments = list_text(options.get("key_developments")) or source_summaries or ["No source summary provided."]
    why_it_matters = list_text(options.get("why_it_matters")) or default_why_it_matters(request)
    potential_implications = list_text(options.get("potential_implications")) or default_implications(request)
    watch_next = list_text(options.get("watch_next")) or default_watch_next(request, sources)
    red_team_checks = list_text(options.get("red_team_checks")) or default_red_team_checks()
    uncertainty = list_text(options.get("uncertainty")) or default_uncertainty()
    confidence = str(options.get("confidence") or estimate_brief_confidence(sources)).strip()
    source_links = [format_source_link(source) for source in sources]

    return NewsBrief(
        headline=headline,
        lead=lead,
        key_developments=key_developments,
        why_it_matters=why_it_matters,
        potential_implications=potential_implications,
        confidence=confidence,
        uncertainty=uncertainty,
        watch_next=watch_next,
        red_team_checks=red_team_checks,
        source_links=source_links,
    )


def render_news_brief_markdown(
    request: dict[str, Any],
    brief: NewsBrief,
    run_id: str,
    now: datetime,
    report_stem: str,
) -> str:
    return f"""---
type: daily_intelligence
status: user_review
created: {now:%Y-%m-%d}
updated: {now:%Y-%m-%d}
source: multiple
confidence: {brief.confidence}
likelihood: monitored
related_project: {request.get("related_project", "")}
tags: {request_tags_json(request)}
run_id: {run_id}
---

# Daily Intelligence: {request["title"]}

## Headline

{brief.headline}

## Summary

{brief.lead}

## Key Developments

{bullet_list(brief.key_developments)}

## Why It Matters

{bullet_list(brief.why_it_matters)}

## Potential Implications

{bullet_list(brief.potential_implications)}

## Confidence / Uncertainty

- Confidence: {brief.confidence}
{bullet_list(brief.uncertainty)}

## What To Watch Next

{bullet_list(brief.watch_next)}

## Red Team Checks

{bullet_list(brief.red_team_checks)}

## Sources

{chr(10).join(brief.source_links)}

## User Review

- Approval: pending
- User corrections:
- Follow-up questions:

## Linked Notes

- Strategic Intelligence: [[{report_stem}]]
"""


def list_text(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def default_headline(request: dict[str, Any], sources: list[dict[str, str]]) -> str:
    if sources:
        return f"{request['title']}: {len(sources)}件のソースから重要シグナルを整理"
    return f"{request['title']}: 追加ソース確認が必要"


def default_why_it_matters(request: dict[str, Any]) -> list[str]:
    decision_context = request.get("decision_context", "")
    items = [
        "The brief converts source updates into a reviewable intelligence item.",
        "Each claim remains traceable to a dated source.",
    ]
    if decision_context:
        items.append(f"Decision context: {decision_context}")
    return items


def default_implications(request: dict[str, Any]) -> list[str]:
    scope = ", ".join(str(item) for item in request.get("scope", [])[:3])
    if scope:
        return [
            f"The update may affect how the user monitors {scope}.",
            "The topic should stay on the watchlist if follow-up sources confirm the same direction.",
        ]
    return ["The topic should stay on the watchlist if follow-up sources confirm the same direction."]


def default_watch_next(request: dict[str, Any], sources: list[dict[str, str]]) -> list[str]:
    configured_scope = [f"Next update related to {item}" for item in request.get("scope", [])[:4]]
    publishers = [source.get("publisher", "") for source in sources if source.get("publisher")]
    publisher_items = [f"Follow-up release from {publisher}" for publisher in publishers[:3]]
    return configured_scope or publisher_items or ["Next official or primary-source update."]


def default_red_team_checks() -> list[str]:
    return [
        "Confirm that every source is still the latest relevant release.",
        "Separate observed facts from forecasts, estimates, and interpretations.",
        "Check whether regional or sector-specific evidence changes the headline judgment.",
    ]


def default_uncertainty() -> list[str]:
    return [
        "Source timing may change the interpretation when newer releases arrive.",
        "A limited source set may omit regional or domain-specific exceptions.",
    ]


def estimate_brief_confidence(sources: list[dict[str, str]]) -> str:
    if not sources:
        return "low"
    high_quality_count = sum(
        1
        for source in sources
        if str(source.get("primary_source", "")).lower() == "true"
        and str(source.get("reliability", "")).lower() == "high"
    )
    if high_quality_count >= 3:
        return "high"
    if high_quality_count >= 1:
        return "medium"
    return "low"


def format_source_link(source: dict[str, str]) -> str:
    title = source.get("title", source.get("heading", "Untitled"))
    url = source.get("url", "")
    publisher = source.get("publisher", "")
    date = source.get("date", "")
    detail = " / ".join(item for item in [publisher, date] if item)
    suffix = f" ({detail})" if detail else ""
    return f"- [{title}]({url}){suffix}"


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def request_tags_json(request: dict[str, Any]) -> str:
    import json

    return json.dumps(request.get("tags", []), ensure_ascii=False)
