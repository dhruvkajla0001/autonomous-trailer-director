"""Deterministic ingestion for policy, rights, audience, and budget source data."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from src.models.constraints import AudienceProfile, BudgetConfig, Constraint, ConstraintMap, Contract, HistoricPerformanceRecord


class ConstraintIngestionError(ValueError):
    """Raised when constraints cannot be used as reliable decision rules."""


def load_constraint_map(
    contracts_path: Path,
    policies_path: Path,
    audiences_path: Path,
) -> ConstraintMap:
    """Load independent source files into a typed, internally consistent constraint map."""
    contracts_data = _load_json(contracts_path, "contracts")
    policies_data = _load_json(policies_path, "policies")
    audiences_data = _load_json(audiences_path, "audiences")

    _require_demo_marker(contracts_data, contracts_path)
    _require_demo_marker(policies_data, policies_path)
    _require_demo_marker(audiences_data, audiences_path)

    try:
        constraint_map = ConstraintMap(
            contracts=[Contract.model_validate(item) for item in _required_list(contracts_data, "contracts", contracts_path)],
            constraints=[Constraint.model_validate(item) for item in _required_list(policies_data, "constraints", policies_path)],
            audiences=[AudienceProfile.model_validate(item) for item in _required_list(audiences_data, "audiences", audiences_path)],
            historic_performance=[
                HistoricPerformanceRecord.model_validate(item)
                for item in _required_list(audiences_data, "historic_performance", audiences_path)
            ],
            budget=BudgetConfig.model_validate(policies_data.get("budget")),
            source_refs=[
                f"file:{contracts_path.as_posix()}",
                f"file:{policies_path.as_posix()}",
                f"file:{audiences_path.as_posix()}",
            ],
        )
    except ValidationError as error:
        raise ConstraintIngestionError(f"Constraint source failed schema validation:\n{error}") from error

    _require_unique("contract ID", (contract.contract_id for contract in constraint_map.contracts))
    _require_unique("contract resource", (contract.resource_id for contract in constraint_map.contracts))
    _require_unique("constraint ID", (constraint.constraint_id for constraint in constraint_map.constraints))
    _require_unique("audience ID", (audience.audience_id for audience in constraint_map.audiences))
    return constraint_map


def _load_json(path: Path, source_name: str) -> dict[str, object]:
    if not path.is_file():
        raise ConstraintIngestionError(f"{source_name.capitalize()} source does not exist: {path}")
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConstraintIngestionError(f"{source_name.capitalize()} source is not valid JSON: {path}") from error
    if not isinstance(loaded, dict):
        raise ConstraintIngestionError(f"{source_name.capitalize()} source must contain a JSON object: {path}")
    return loaded


def _required_list(data: dict[str, object], key: str, path: Path) -> list[object]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ConstraintIngestionError(f"{path} must contain a list at {key!r}")
    return value


def _require_demo_marker(data: dict[str, object], path: Path) -> None:
    if data.get("is_demo_data") is not True:
        raise ConstraintIngestionError(f"{path} must explicitly set is_demo_data to true")


def _require_unique(kind: str, identifiers: object) -> None:
    seen: set[str] = set()
    for identifier in identifiers:  # type: ignore[union-attr]
        if identifier in seen:
            raise ConstraintIngestionError(f"Duplicate {kind}: {identifier}")
        seen.add(identifier)
