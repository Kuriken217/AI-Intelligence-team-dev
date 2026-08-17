from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_THEME_REGISTRY = Path("config/daily_intelligence_themes.json")


@dataclass(frozen=True)
class ThemeRegistry:
    themes: dict[str, dict[str, Any]]


def load_theme_registry(path: Path = DEFAULT_THEME_REGISTRY) -> ThemeRegistry:
    payload = json.loads(path.read_text(encoding="utf-8"))
    themes = payload.get("themes")
    if not isinstance(themes, dict) or not themes:
        raise ValueError("Theme registry must contain a non-empty 'themes' object.")
    return ThemeRegistry(themes=themes)


def list_theme_rows(registry: ThemeRegistry) -> list[tuple[str, str, str]]:
    rows = []
    for theme_id, theme in sorted(registry.themes.items()):
        rows.append((theme_id, str(theme.get("display_name", theme_id)), str(theme.get("priority", ""))))
    return rows


def build_request_from_theme(
    registry: ThemeRegistry,
    theme_id: str,
    title: str | None = None,
    related_project: str | None = None,
) -> dict[str, Any]:
    if theme_id not in registry.themes:
        available = ", ".join(sorted(registry.themes))
        raise ValueError(f"Unknown theme '{theme_id}'. Available themes: {available}")

    theme = registry.themes[theme_id]
    request = {
        "title": title or theme["title"],
        "objective": theme["objective"],
        "decision_context": theme["decision_context"],
        "scope": list(theme.get("scope", [])),
        "related_project": related_project or theme.get("related_project", "Daily Intelligence"),
        "priority": theme.get("priority", "medium"),
        "requested_output": "Daily Intelligence / News Brief",
        "news_brief": dict(theme.get("news_brief", {})),
        "tags": list(theme.get("tags", [])),
    }
    return request


def build_url_source_template(registry: ThemeRegistry, theme_id: str) -> dict[str, Any]:
    if theme_id not in registry.themes:
        available = ", ".join(sorted(registry.themes))
        raise ValueError(f"Unknown theme '{theme_id}'. Available themes: {available}")

    theme = registry.themes[theme_id]
    return {
        "theme_id": theme_id,
        "source_guidance": list(theme.get("source_guidance", [])),
        "sources": [
            {
                "title": "",
                "url": "",
                "type": "",
                "date": "",
                "publisher": "",
                "primary_source": True,
                "reliability": "high",
                "summary": ""
            }
        ],
    }


def write_theme_request(
    registry_path: Path,
    theme_id: str,
    output_path: Path,
    title: str | None = None,
    related_project: str | None = None,
) -> Path:
    registry = load_theme_registry(registry_path)
    request = build_request_from_theme(registry, theme_id, title=title, related_project=related_project)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def write_theme_url_template(registry_path: Path, theme_id: str, output_path: Path) -> Path:
    registry = load_theme_registry(registry_path)
    template = build_url_source_template(registry, theme_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
