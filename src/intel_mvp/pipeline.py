from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .contracts import validate_information_request, validate_named_contract
    from .delta import build_prior_knowledge_delta
    from .news_brief import build_news_brief, render_news_brief_markdown
    from .prior_knowledge import find_related_notes, load_user_settings, summarize_related_notes
    from .stages import (
        build_analysis_packet,
        build_integrated_intelligence,
        build_knowledge_keeper_packet,
        build_mission_brief,
        build_red_team_review,
        build_source_digest,
        build_strategy_packet,
    )
except ImportError:
    from contracts import validate_information_request, validate_named_contract
    from delta import build_prior_knowledge_delta
    from news_brief import build_news_brief, render_news_brief_markdown
    from prior_knowledge import find_related_notes, load_user_settings, summarize_related_notes
    from stages import (
        build_analysis_packet,
        build_integrated_intelligence,
        build_knowledge_keeper_packet,
        build_mission_brief,
        build_red_team_review,
        build_source_digest,
        build_strategy_packet,
    )


VAULT_FOLDERS = [
    "00_Inbox",
    "10_Daily_Intelligence",
    "20_Project_Intelligence",
    "30_Strategic_Intelligence",
    "40_Knowledge",
    "50_Hypotheses",
    "60_Decisions",
    "70_Actions_and_Results",
    "90_Sources",
    "Templates",
]


@dataclass(frozen=True)
class PipelineResult:
    run_id: str
    created_notes: list[Path]
    run_files: list[Path]
    mobile_files: list[Path] = field(default_factory=list)


def run_pipeline(request_path: Path, sources_path: Path, vault_path: Path, run_root_path: Path | None = None) -> PipelineResult:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    contracts_path = request_path.parent.parent / "config" / "io_schemas.json"
    if contracts_path.exists():
        validation = validate_information_request(request, contracts_path)
        if not validation.valid:
            missing = ", ".join(validation.missing_fields)
            raise ValueError(f"Information request is missing required fields: {missing}")

    source_text = sources_path.read_text(encoding="utf-8")
    sources = parse_source_digest(source_text)

    now = datetime.now()
    run_id = now.strftime("%Y%m%d-%H%M%S-%f")
    slug = slugify(request["title"])

    ensure_vault(vault_path)
    write_templates(vault_path)

    run_path = (run_root_path or vault_path.parent / "runs") / run_id
    run_path.mkdir(parents=True, exist_ok=True)

    prior_knowledge_summary = build_prior_knowledge_summary(request, request_path.parent.parent / "config" / "user_settings.json")
    mission_brief = build_mission_brief(request, run_id, prior_knowledge_summary)
    source_digest = build_source_digest(sources)
    prior_knowledge_delta = build_prior_knowledge_delta(prior_knowledge_summary, source_digest)
    analysis_packet = build_analysis_packet(source_digest)
    integrated_intelligence = build_integrated_intelligence(analysis_packet)
    red_team_review = build_red_team_review(integrated_intelligence)
    strategy_packet = build_strategy_packet(red_team_review)

    run_files = [
        write_json(run_path / "00_prior_knowledge.json", prior_knowledge_summary),
        write_stage_json(run_path / "01_mission_brief.json", mission_brief, "mission_brief", contracts_path),
        write_stage_json(run_path / "02_source_digest.json", source_digest, "source_digest", contracts_path),
        write_json(run_path / "03_prior_knowledge_delta.json", prior_knowledge_delta),
        write_stage_json(run_path / "04_analysis_packet.json", analysis_packet, "analysis_packet", contracts_path),
        write_stage_json(
            run_path / "05_integrated_intelligence.json",
            integrated_intelligence,
            "integrated_intelligence",
            contracts_path,
        ),
        write_stage_json(run_path / "06_red_team_review.json", red_team_review, "red_team_review", contracts_path),
        write_stage_json(run_path / "07_strategy_packet.json", strategy_packet, "strategy_packet", contracts_path),
    ]

    created_notes = []
    if should_write_daily_intelligence(request):
        created_notes.append(write_daily_intelligence_note(vault_path, request, sources, run_id, now, slug))
    created_notes.extend(
        [
            write_source_note(vault_path, request, sources, run_id, now, slug),
            write_intelligence_report(vault_path, request, sources, run_id, now, slug),
            write_hypothesis_note(vault_path, request, sources, run_id, now, slug),
            write_decision_note(vault_path, request, run_id, now, slug),
            write_result_note(vault_path, request, run_id, now, slug),
        ]
    )
    created_notes.append(write_review_queue_note(vault_path, request, created_notes, run_id, now, slug))

    knowledge_keeper_packet = build_knowledge_keeper_packet([str(note) for note in created_notes])
    run_files.append(write_json(run_path / "08_knowledge_keeper_packet.json", knowledge_keeper_packet))

    return PipelineResult(run_id=run_id, created_notes=created_notes, run_files=run_files)


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_prior_knowledge_summary(request: dict[str, Any], settings_path: Path) -> dict[str, Any]:
    if not settings_path.exists():
        return {"enabled": False, "related_note_count": 0, "notes": []}

    settings = load_user_settings(settings_path)
    options = settings.get("prior_knowledge", {})
    if not options.get("enabled", False):
        return {"enabled": False, "related_note_count": 0, "notes": []}

    vault_path = Path(settings.get("obsidian_vault_path", ""))
    notes = find_related_notes(
        vault_path=vault_path,
        request=request,
        max_notes=int(options.get("max_notes", 10)),
        max_excerpt_chars=int(options.get("max_excerpt_chars", 500)),
        exclude_folders=list(options.get("exclude_folders", [])),
        ignored_terms=list(options.get("ignored_terms", [])),
        min_score=int(options.get("min_score", 1)),
    )
    summary = summarize_related_notes(notes)
    summary["enabled"] = True
    summary["vault_path"] = str(vault_path)
    return summary


def write_stage_json(path: Path, payload: dict[str, Any], contract_name: str, contracts_path: Path) -> Path:
    if contracts_path.exists():
        validation = validate_named_contract(payload, contract_name, contracts_path)
        if not validation.valid:
            missing = ", ".join(validation.missing_fields)
            raise ValueError(f"{contract_name} is missing required fields: {missing}")
    return write_json(path, payload)


def ensure_vault(vault_path: Path) -> None:
    for folder in VAULT_FOLDERS:
        (vault_path / folder).mkdir(parents=True, exist_ok=True)


def write_templates(vault_path: Path) -> None:
    templates = {
        "Intelligence Report.md": intelligence_template(),
        "Decision Note.md": decision_template(),
        "Result Note.md": result_template(),
        "Source Note.md": source_template(),
    }
    for name, body in templates.items():
        path = vault_path / "Templates" / name
        if not path.exists():
            path.write_text(body, encoding="utf-8")


def parse_source_digest(source_text: str) -> list[dict[str, str]]:
    sections = re.split(r"\n##\s+", source_text)
    sources: list[dict[str, str]] = []
    for section in sections[1:]:
        item: dict[str, str] = {"heading": section.splitlines()[0].strip()}
        for line in section.splitlines()[1:]:
            match = re.match(r"-\s*([A-Za-z_]+):\s*(.*)", line.strip())
            if match:
                item[match.group(1).lower()] = match.group(2).strip()
        if item:
            sources.append(item)
    return sources


def should_write_daily_intelligence(request: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(request.get("title", "")),
            str(request.get("requested_output", "")),
            str(request.get("objective", "")),
        ]
    ).lower()
    return any(token in text for token in ["daily intelligence", "news", "ニュース"])


def write_daily_intelligence_note(
    vault_path: Path,
    request: dict[str, Any],
    sources: list[dict[str, str]],
    run_id: str,
    now: datetime,
    slug: str,
) -> Path:
    daily_stem = note_stem(now, slug, run_id, "daily_intelligence")
    report_stem = note_stem(now, slug, run_id, "intelligence_report")
    path = vault_path / "10_Daily_Intelligence" / f"{daily_stem}.md"
    brief = build_news_brief(request, sources, now)
    body = render_news_brief_markdown(request, brief, run_id, now, report_stem)
    path.write_text(body, encoding="utf-8")
    return path


def write_source_note(
    vault_path: Path,
    request: dict[str, Any],
    sources: list[dict[str, str]],
    run_id: str,
    now: datetime,
    slug: str,
) -> Path:
    source_stem = note_stem(now, slug, run_id, "source_digest")
    path = vault_path / "90_Sources" / f"{source_stem}.md"
    source_blocks = "\n\n".join(format_source(source, index + 1) for index, source in enumerate(sources))
    body = f"""---
type: source_digest
status: collected
created: {now:%Y-%m-%d}
updated: {now:%Y-%m-%d}
source: multiple
confidence: medium
likelihood:
related_project: {request.get("related_project", "")}
tags: {json.dumps(request.get("tags", []), ensure_ascii=False)}
run_id: {run_id}
---

# Source Digest: {request["title"]}

## Mission Context

- Objective: {request.get("objective", "")}
- Decision Context: {request.get("decision_context", "")}

## Sources

{source_blocks}
"""
    path.write_text(body, encoding="utf-8")
    return path


def write_intelligence_report(
    vault_path: Path,
    request: dict[str, Any],
    sources: list[dict[str, str]],
    run_id: str,
    now: datetime,
    slug: str,
) -> Path:
    report_stem = note_stem(now, slug, run_id, "intelligence_report")
    source_stem = note_stem(now, slug, run_id, "source_digest")
    hypothesis_stem = note_stem(now, slug, run_id, "hypothesis")
    decision_stem = note_stem(now, slug, run_id, "decision")
    result_stem = note_stem(now, slug, run_id, "result")
    path = vault_path / "30_Strategic_Intelligence" / f"{report_stem}.md"
    fact_lines = "\n".join(f"- {source.get('summary', 'No summary provided')}" for source in sources)
    source_links = "\n".join(f"- [{source.get('title', source.get('heading', 'Untitled'))}]({source.get('url', '')})" for source in sources)
    first_fact = next((source.get("summary", "") for source in sources if source.get("summary")), "")
    body = f"""---
type: strategic_intelligence
status: user_review
created: {now:%Y-%m-%d}
updated: {now:%Y-%m-%d}
source: multiple
confidence: medium
likelihood: to_be_assessed
related_project: {request.get("related_project", "")}
tags: {json.dumps(request.get("tags", []), ensure_ascii=False)}
run_id: {run_id}
---

# Strategic Intelligence: {request["title"]}

## 1. Information Request

{request.get("objective", "")}

## 2. Collection

{source_links}

## 3. Fact Candidates

{fact_lines}

## 4. Analysis

- The source set is weighted toward official public-agency information, which improves traceability.
- Observed indicators, forecast statements, and background dataset notes should be kept separate in the final judgment.
- The most important near-term question is whether the signal remains consistent across the next official updates.

## 5. Integrated Intelligence

{first_fact or "The available source set is sufficient for a monitored intelligence brief, but not for a final conclusion without follow-up validation."}

The topic is suitable for user review because the sources are traceable, dated, and tied to concrete monitoring indicators.

## 6. Red Team Review

- Confirm that each source is the latest relevant official release before publishing.
- Avoid treating forecasts as already-observed outcomes.
- Regional impacts may differ materially from global indicators.
- Missing information: next release timing, baseline periods, regional exceptions, and impact evidence.

## 7. Strategic Recommendation

- Publish as a monitored intelligence brief if the user needs situational awareness now.
- Track the next official updates and revise confidence when new data arrives.
- Preserve source links and dates so the brief can be audited later.

## 8. User Review

- Approval: pending
- User corrections:
- Decision:
- Follow-up questions:

## 9. Links

- Source Digest: [[{source_stem}]]
- Hypothesis: [[{hypothesis_stem}]]
- Decision: [[{decision_stem}]]
- Result: [[{result_stem}]]
"""
    path.write_text(body, encoding="utf-8")
    return path


def write_hypothesis_note(
    vault_path: Path,
    request: dict[str, Any],
    sources: list[dict[str, str]],
    run_id: str,
    now: datetime,
    slug: str,
) -> Path:
    path = vault_path / "50_Hypotheses" / f"{note_stem(now, slug, run_id, 'hypothesis')}.md"
    body = f"""---
type: hypothesis
status: draft
created: {now:%Y-%m-%d}
updated: {now:%Y-%m-%d}
source: multiple
confidence: low
likelihood: to_be_assessed
related_project: {request.get("related_project", "")}
tags: {json.dumps(request.get("tags", []), ensure_ascii=False)}
run_id: {run_id}
---

# Hypothesis: {request["title"]}

## Hypothesis

If multiple official indicators continue to point in the same direction, this topic should remain an active intelligence watch item.

## Supporting Evidence

{chr(10).join(f"- {source.get('summary', 'No summary provided')}" for source in sources)}

## What Would Increase Confidence

- Follow-up official releases confirm the same signal
- Independent agencies report consistent indicators
- Regional impact evidence aligns with the global pattern
- Baseline periods and methods are clearly comparable

## What Would Decrease Confidence

- Later releases revise the signal downward
- Indicators diverge across agencies or methods
- Regional exceptions dominate the practical impact
- The source set proves outdated or incomplete

## Next Research

- Add the next official update
- Compare observed records with forecast products
- Track regional impacts and policy-relevant consequences
"""
    path.write_text(body, encoding="utf-8")
    return path


def write_decision_note(vault_path: Path, request: dict[str, Any], run_id: str, now: datetime, slug: str) -> Path:
    report_stem = note_stem(now, slug, run_id, "intelligence_report")
    path = vault_path / "60_Decisions" / f"{note_stem(now, slug, run_id, 'decision')}.md"
    body = f"""---
type: decision
status: pending
created: {now:%Y-%m-%d}
updated: {now:%Y-%m-%d}
source: "[[{report_stem}]]"
confidence:
likelihood:
related_project: {request.get("related_project", "")}
tags: {json.dumps(request.get("tags", []), ensure_ascii=False)}
run_id: {run_id}
---

# Decision: {request["title"]}

## Decision To Make

{request.get("decision_context", "")}

## Options

- Approve as active intelligence theme
- Keep in watchlist
- Reject or defer

## User Decision

- Decision:
- Reason:
- Date:

## Follow-up Actions

- [ ] Add the next official update
- [ ] Compare regional impact evidence
- [ ] Review decision after new evidence
"""
    path.write_text(body, encoding="utf-8")
    return path


def write_result_note(vault_path: Path, request: dict[str, Any], run_id: str, now: datetime, slug: str) -> Path:
    decision_stem = note_stem(now, slug, run_id, "decision")
    path = vault_path / "70_Actions_and_Results" / f"{note_stem(now, slug, run_id, 'result')}.md"
    body = f"""---
type: result
status: waiting
created: {now:%Y-%m-%d}
updated: {now:%Y-%m-%d}
source: "[[{decision_stem}]]"
confidence:
likelihood:
related_project: {request.get("related_project", "")}
tags: {json.dumps(request.get("tags", []), ensure_ascii=False)}
run_id: {run_id}
---

# Result: {request["title"]}

## Action Taken

- 

## Result

- 

## Feedback For Future Intelligence

- What was useful:
- What was wrong:
- What should be tracked next:

## Knowledge Update

- [ ] Update related hypothesis
- [ ] Update project intelligence
- [ ] Add new sources
"""
    path.write_text(body, encoding="utf-8")
    return path


def write_review_queue_note(
    vault_path: Path,
    request: dict[str, Any],
    notes: list[Path],
    run_id: str,
    now: datetime,
    slug: str,
) -> Path:
    path = vault_path / "00_Inbox" / f"{note_stem(now, slug, run_id, 'review_queue')}.md"
    links = "\n".join(f"- [ ] [[{note.stem}]]" for note in notes)
    body = f"""---
type: review_queue
status: user_review
created: {now:%Y-%m-%d}
updated: {now:%Y-%m-%d}
source: multiple
confidence:
likelihood:
related_project: {request.get("related_project", "")}
tags: {json.dumps(request.get("tags", []), ensure_ascii=False)}
run_id: {run_id}
---

# Review Queue: {request["title"]}

## Review Items

{links}

## User Review Steps

- [ ] Read the Strategic Intelligence Report
- [ ] Review Red Team objections
- [ ] Approve, reject, or move to watchlist
- [ ] Record decision
- [ ] Record result after action
"""
    path.write_text(body, encoding="utf-8")
    return path


def format_source(source: dict[str, str], index: int) -> str:
    title = source.get("title", source.get("heading", f"Source {index}"))
    return f"""### Source {index}: {title}

- URL: {source.get("url", "")}
- Type: {source.get("type", "")}
- Date: {source.get("date", "")}
- Publisher: {source.get("publisher", "")}
- Primary Source: {source.get("primary_source", "")}
- Reliability: {source.get("reliability", "")}
- Summary: {source.get("summary", "")}"""


def slugify(value: str) -> str:
    filename_safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "", value).strip()
    filename_safe = re.sub(r"\s+", "-", filename_safe)
    filename_safe = re.sub(r"-+", "-", filename_safe)
    return filename_safe[:80].strip(".-") or "intelligence-request"


def note_stem(now: datetime, slug: str, run_id: str, kind: str) -> str:
    return f"{now:%Y-%m-%d}_{slug}_{run_id}_{kind}"


def intelligence_template() -> str:
    return """---
type: strategic_intelligence
status: user_review
created:
updated:
source:
confidence:
likelihood:
related_project:
tags:
run_id:
---

# Strategic Intelligence

## Information Request

## Collection

## Fact Candidates

## Analysis

## Integrated Intelligence

## Red Team Review

## Strategic Recommendation

## User Review
"""


def decision_template() -> str:
    return """---
type: decision
status: pending
created:
updated:
source:
confidence:
likelihood:
related_project:
tags:
run_id:
---

# Decision

## Decision To Make

## Options

## User Decision

## Follow-up Actions
"""


def result_template() -> str:
    return """---
type: result
status: waiting
created:
updated:
source:
confidence:
likelihood:
related_project:
tags:
run_id:
---

# Result

## Action Taken

## Result

## Feedback For Future Intelligence

## Knowledge Update
"""


def source_template() -> str:
    return """---
type: source_digest
status: collected
created:
updated:
source:
confidence:
likelihood:
related_project:
tags:
run_id:
---

# Source Digest

## Mission Context

## Sources
"""
