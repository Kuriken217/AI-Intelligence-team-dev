from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_vault_rules(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def required_frontmatter_fields(rules: dict[str, Any]) -> list[str]:
    return list(rules.get("frontmatter_required", []))


def missing_frontmatter_fields(frontmatter: dict[str, Any], rules: dict[str, Any]) -> list[str]:
    required = required_frontmatter_fields(rules)
    return [field for field in required if field not in frontmatter]

