from __future__ import annotations


def is_primary_source(source: dict[str, str]) -> bool:
    value = str(source.get("primary_source", "")).strip().lower()
    return value in {"true", "yes", "1", "primary"}


def reliability_level(source: dict[str, str]) -> str:
    value = str(source.get("reliability", "")).strip().lower()
    return value if value in {"high", "medium", "low"} else "unknown"


def source_quality_gaps(sources: list[dict[str, str]]) -> list[str]:
    gaps: list[str] = []
    primary_count = sum(1 for source in sources if is_primary_source(source))
    useful_reliability_count = sum(1 for source in sources if reliability_level(source) in {"high", "medium"})

    if len(sources) < 3:
        gaps.append("Fewer than three sources are included.")
    if primary_count == 0:
        gaps.append("No primary source is currently included.")
    if useful_reliability_count < 2:
        gaps.append("Fewer than two high or medium reliability sources are included.")

    return gaps

