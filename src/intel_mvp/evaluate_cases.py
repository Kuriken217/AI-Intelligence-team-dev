from __future__ import annotations

import json
from pathlib import Path

try:
    from .evaluation import evaluate_run
    from .pipeline import run_pipeline
except ImportError:
    from evaluation import evaluate_run
    from pipeline import run_pipeline


CASES = [
    ("liquid_cooling", "liquid_cooling_request.json", "liquid_cooling_sources.md"),
    ("obsidian_ai_workflow", "obsidian_ai_workflow_request.json", "obsidian_ai_workflow_sources.md"),
    ("agent_red_team", "agent_red_team_request.json", "agent_red_team_sources.md"),
]


def run_evaluation_cases(
    cases_path: Path = Path("examples/evaluation_cases"),
    vault_path: Path = Path("evaluation_vault"),
    report_path: Path = Path("reports/evaluation_cases_summary.json"),
) -> Path:
    results = []
    for case_id, request_name, sources_name in CASES:
        pipeline_result = run_pipeline(cases_path / request_name, cases_path / sources_name, vault_path)
        run_path = vault_path.parent / "runs" / pipeline_result.run_id
        evaluation = evaluate_run(run_path)
        evaluation["case_id"] = case_id
        evaluation["run_id"] = pipeline_result.run_id
        results.append(evaluation)

    summary = {
        "case_count": len(results),
        "passed_count": sum(1 for result in results if result["passed"]),
        "all_passed": all(result["passed"] for result in results),
        "results": results,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path


def main() -> int:
    report_path = run_evaluation_cases()
    print(f"Wrote evaluation cases summary: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

