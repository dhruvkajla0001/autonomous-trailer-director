"""Tests for deterministic source ingestion of rights, policies, and audiences."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.repository.constraint_repository import ConstraintIngestionError, load_constraint_map
from src.tools.constraint_lookup import ConstraintLookup, ConstraintNotFoundError

ROOT = Path(__file__).resolve().parents[1]


def paths() -> tuple[Path, Path, Path]:
    return (
        ROOT / "data/contracts/contracts_demo.json",
        ROOT / "data/policies/policies_demo.json",
        ROOT / "data/audience/audiences_demo.json",
    )


def test_constraint_map_is_loaded_and_looked_up_fail_closed() -> None:
    lookup = ConstraintLookup(load_constraint_map(*paths()))

    assert lookup.contract_for("track_folk_01").promotional_use_allowed is True
    assert lookup.audience("family").display_name == "Family viewers"
    assert "policy_family_rating" in {rule.constraint_id for rule in lookup.constraints_for("family")}
    with pytest.raises(ConstraintNotFoundError, match="No contract"):
        lookup.contract_for("unknown_track")


def test_duplicate_contract_resource_is_rejected(tmp_path: Path) -> None:
    contracts_path, policies_path, audiences_path = paths()
    contracts = json.loads(contracts_path.read_text(encoding="utf-8"))
    duplicate = dict(contracts["contracts"][0])
    duplicate["contract_id"] = "another_contract"
    contracts["contracts"].append(duplicate)
    malformed_contracts = tmp_path / "contracts.json"
    malformed_contracts.write_text(json.dumps(contracts), encoding="utf-8")

    with pytest.raises(ConstraintIngestionError, match="Duplicate contract resource"):
        load_constraint_map(malformed_contracts, policies_path, audiences_path)
