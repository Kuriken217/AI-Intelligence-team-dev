from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from .evaluation import write_evaluation_report
    from .obsidian_direct import ThemeObsidianRunResult, run_theme_feeds_to_obsidian
except ImportError:
    from evaluation import write_evaluation_report
    from obsidian_direct import ThemeObsidianRunResult, run_theme_feeds_to_obsidian


DEFAULT_DAILY_RUN_CONFIG = Path("config/daily_runs.json")


@dataclass(frozen=True)
class DailyRunResult:
    profile: str
    theme_id: str
    run_id: str
    run_path: Path
    request_path: Path
    source_digest_path: Path
    evaluation_path: Path
    summary_path: Path
    latest_summary_path: Path
    evaluation: dict[str, Any]
    theme_result: ThemeObsidianRunResult


def load_daily_run_config(config_path: Path = DEFAULT_DAILY_RUN_CONFIG) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Daily run config not found: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def run_daily_profile(
    profile_name: str,
    config_path: Path = DEFAULT_DAILY_RUN_CONFIG,
    limit_override: int | None = None,
) -> DailyRunResult:
    config = load_daily_run_config(config_path)
    profiles = config.get("profiles", {})
    if profile_name not in profiles:
        available = ", ".join(sorted(profiles)) or "(none)"
        raise ValueError(f"Unknown daily run profile '{profile_name}'. Available profiles: {available}")

    profile = profiles[profile_name]
    theme_id = require_text(profile, "theme")
    settings_path = Path(profile.get("settings", "config/user_settings.json"))
    registry_path = Path(profile.get("registry", "config/daily_intelligence_themes.json"))
    work_dir = Path(profile.get("work_dir", "work/daily_runs"))
    evaluation_dir = Path(profile.get("evaluation_dir", "work/reports/daily_runs"))
    limit = limit_override if limit_override is not None else int(profile.get("limit", 5))
    timeout_seconds = int(profile.get("timeout_seconds", profile.get("timeout", 15)))
    enrich = bool(profile.get("enrich", False))
    title = optional_text(profile, "title")
    related_project = optional_text(profile, "related_project")

    theme_result = run_theme_feeds_to_obsidian(
        theme_id=theme_id,
        settings_path=settings_path,
        registry_path=registry_path,
        work_dir=work_dir,
        title=title,
        related_project=related_project,
        limit=limit,
        enrich=enrich,
        timeout_seconds=timeout_seconds,
    )

    pipeline_result = theme_result.url_run_result.pipeline_result
    run_path = pipeline_result.run_files[0].parent
    evaluation_path = evaluation_dir / profile_name / f"{pipeline_result.run_id}.evaluation.json"
    write_evaluation_report(run_path, evaluation_path)
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))

    summary = build_daily_summary(profile_name, theme_id, theme_result, evaluation, run_path)
    summary_dir = work_dir / profile_name / "summaries"
    summary_path = summary_dir / f"{pipeline_result.run_id}.summary.json"
    latest_summary_path = summary_dir / "latest_summary.json"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_text = json.dumps(summary, ensure_ascii=False, indent=2)
    summary_path.write_text(summary_text, encoding="utf-8")
    latest_summary_path.write_text(summary_text, encoding="utf-8")

    return DailyRunResult(
        profile=profile_name,
        theme_id=theme_id,
        run_id=pipeline_result.run_id,
        run_path=run_path,
        request_path=theme_result.request_path,
        source_digest_path=theme_result.url_run_result.source_digest_path,
        evaluation_path=evaluation_path,
        summary_path=summary_path,
        latest_summary_path=latest_summary_path,
        evaluation=evaluation,
        theme_result=theme_result,
    )


def build_daily_summary(
    profile_name: str,
    theme_id: str,
    theme_result: ThemeObsidianRunResult,
    evaluation: dict[str, Any],
    run_path: Path,
) -> dict[str, Any]:
    pipeline_result = theme_result.url_run_result.pipeline_result
    return {
        "profile": profile_name,
        "theme_id": theme_id,
        "run_id": pipeline_result.run_id,
        "run_path": str(run_path),
        "request_path": str(theme_result.request_path),
        "source_digest_path": str(theme_result.url_run_result.source_digest_path),
        "evaluation": evaluation,
        "obsidian_notes": [str(path) for path in pipeline_result.created_notes],
        "mobile_files": [str(path) for path in pipeline_result.mobile_files],
    }


def require_text(payload: dict[str, Any], key: str) -> str:
    value = str(payload.get(key, "")).strip()
    if not value:
        raise ValueError(f"Daily run profile requires '{key}'.")
    return value


def optional_text(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None
