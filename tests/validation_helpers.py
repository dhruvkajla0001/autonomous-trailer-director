"""Shared factories for independent validation tests."""

from __future__ import annotations

from pathlib import Path

from src.agents.planner_agent import PlannerAgent
from src.agents.story_agent import StoryAgent
from src.agents.verifier_agent import VerifierAgent
from src.models.constraints import ConstraintMap
from src.models.story import StoryMap
from src.models.trailer import TrailerPlan
from src.repository.constraint_repository import load_constraint_map

ROOT = Path(__file__).resolve().parents[1]


def verified_context() -> tuple[StoryMap, ConstraintMap, VerifierAgent]:
    """Build isolated deterministic source state for a validator test."""
    story = StoryAgent().build_story_map(ROOT / "data/episode/episode_demo.json")
    constraints = load_constraint_map(
        ROOT / "data/contracts/contracts_demo.json",
        ROOT / "data/policies/policies_demo.json",
        ROOT / "data/audience/audiences_demo.json",
    )
    return story, constraints, VerifierAgent(story, constraints)


def family_plan() -> TrailerPlan:
    """Return a fresh source-grounded candidate plan for one focused test."""
    story, constraints, _ = verified_context()
    return PlannerAgent(story, constraints).plan_for_audience("family")
