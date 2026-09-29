"""Executable checks for the Phase 2 source-of-truth fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.models.constraints import AudienceProfile, BudgetConfig, Constraint, Contract, ConstraintMap
from src.models.story import Scene, StoryMap

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict[str, object]:
    """Load a committed deterministic demo fixture."""
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_demo_fixtures_validate_as_source_of_truth() -> None:
    """Every mock record must satisfy the typed contract before agents consume it."""
    story = StoryMap.model_validate(load_json("data/episode/episode_demo.json"))
    contracts = load_json("data/contracts/contracts_demo.json")
    policies = load_json("data/policies/policies_demo.json")
    audiences = load_json("data/audience/audiences_demo.json")

    constraint_map = ConstraintMap(
        contracts=[Contract.model_validate(item) for item in contracts["contracts"]],  # type: ignore[index]
        constraints=[Constraint.model_validate(item) for item in policies["constraints"]],  # type: ignore[index]
        audiences=[AudienceProfile.model_validate(item) for item in audiences["audiences"]],  # type: ignore[index]
        historic_performance=[],
        budget=BudgetConfig.model_validate(policies["budget"]),  # type: ignore[index]
        source_refs=["demo:constraint_map"],
    )

    assert story.is_demo_data is True
    assert len(story.scenes) == 8
    assert any(spoiler.severity == "major" for spoiler in story.spoilers)
    assert any(contract.promotional_use_allowed is False for contract in constraint_map.contracts)


def test_scene_rejects_impossible_timecode_range() -> None:
    """Invalid input fails before it can reach a planner or verifier."""
    scene = {
        "scene_id": "bad_scene",
        "source_in": "00:01:10.000",
        "source_out": "00:01:00.000",
        "title": "Invalid",
        "description": "This record must be rejected.",
        "characters": [],
        "actors": [],
        "source_refs": ["test:bad_scene"],
    }

    with pytest.raises(ValidationError, match="source_out must be after source_in"):
        Scene.model_validate(scene)
