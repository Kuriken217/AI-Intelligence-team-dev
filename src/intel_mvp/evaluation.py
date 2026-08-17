from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_RUN_FILES = [
    "00_prior_knowledge.json",
    "01_mission_brief.json",
    "02_source_digest.json",
    "03_prior_knowledge_delta.json",
    "04_analysis_packet.json",
    "05_integrated_intelligence.json",
    "06_red_team_review.json",
    "07_strategy_packet.json",
    "08_knowledge_keeper_packet.json",
]


def evaluate_run(run_path: Path) -> dict[str, Any]:
    stage_data = load_stage_data(run_path)
    scores = {
        "completion": score_completion(run_path),
        "traceability": score_traceability(stage_data.get("02_source_digest.json", {})),
        "red_team_quality": score_red_team(stage_data.get("06_red_team_review.json", {})),
        "actionability": score_actionability(stage_data.get("07_strategy_packet.json", {})),
        "reviewability": score_reviewability(stage_data.get("08_knowledge_keeper_packet.json", {})),
    }
    total = sum(scores.values())
    return {
        "run_path": str(run_path),
        "score": total,
        "passed": total >= 80,
        "scores": scores,
        "missing_files": [name for name in REQUIRED_RUN_FILES if not (run_path / name).exists()],
        "summary": summarize_score(total),
    }


def load_stage_data(run_path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for name in REQUIRED_RUN_FILES:
        path = run_path / name
        if not path.exists():
            continue
        data[name] = json.loads(path.read_text(encoding="utf-8"))
    return data


def score_completion(run_path: Path) -> int:
    existing_count = sum(1 for name in REQUIRED_RUN_FILES if (run_path / name).exists())
    return round(25 * existing_count / len(REQUIRED_RUN_FILES))


def score_traceability(source_digest: dict[str, Any]) -> int:
    score = 0
    if source_digest.get("sources"):
        score += 10
    if source_digest.get("fact_candidates"):
        score += 7
    if "collection_gaps" in source_digest:
        score += 3
    return score


def score_red_team(red_team_review: dict[str, Any]) -> int:
    score = 0
    if red_team_review.get("counterpoints"):
        score += 7
    if red_team_review.get("missing_information"):
        score += 5
    if red_team_review.get("confidence_adjustments"):
        score += 4
    if red_team_review.get("must_verify"):
        score += 4
    return score


def score_actionability(strategy_packet: dict[str, Any]) -> int:
    score = 0
    if strategy_packet.get("recommendation"):
        score += 5
    if strategy_packet.get("options"):
        score += 5
    if strategy_packet.get("next_actions"):
        score += 5
    if strategy_packet.get("decision_prompt"):
        score += 5
    return score


def score_reviewability(knowledge_keeper_packet: dict[str, Any]) -> int:
    score = 0
    if knowledge_keeper_packet.get("notes"):
        score += 10
    if knowledge_keeper_packet.get("review_queue"):
        score += 5
    return score


def summarize_score(score: int) -> str:
    if score >= 90:
        return "Strong MVP run. Ready for user review."
    if score >= 80:
        return "Passing MVP run. Review improvements before relying on it."
    return "Incomplete MVP run. Fix missing or weak stages before user review."


def write_evaluation_report(run_path: Path, output_path: Path) -> Path:
    result = evaluate_run(run_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path

