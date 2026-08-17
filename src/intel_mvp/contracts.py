from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    missing_fields: list[str]


def load_contracts(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_required_fields(payload: dict[str, Any], schema: dict[str, Any]) -> ValidationResult:
    required = schema.get("required", [])
    missing = [field for field in required if field not in payload or payload[field] in (None, "", [])]
    return ValidationResult(valid=not missing, missing_fields=missing)


def validate_information_request(request: dict[str, Any], contracts_path: Path) -> ValidationResult:
    contracts = load_contracts(contracts_path)
    return validate_required_fields(request, contracts["information_request"])


def validate_named_contract(payload: dict[str, Any], contract_name: str, contracts_path: Path) -> ValidationResult:
    contracts = load_contracts(contracts_path)
    if contract_name not in contracts:
        raise KeyError(f"Unknown contract: {contract_name}")
    return validate_required_fields(payload, contracts[contract_name])
