"""Behavior tests for audience-first, source-grounded candidate planning."""

from __future__ import annotations

from pathlib import Path

from src.agents.planner_agent import PlannerAgent
from src.agents.story_agent import StoryAgent
from src.repository.constraint_repository import load_constraint_map

ROOT = Path(__file__).resolve().parents[1]


def build_planner() -> PlannerAgent:
    story_map = StoryAgent().build_story_map(ROOT / "data/episode/episode_demo.json")
    constraint_map = load_constraint_map(
        ROOT / "data/contracts/contracts_demo.json",
        ROOT / "data/policies/policies_demo.json",
        ROOT / "data/audience/audiences_demo.json",
    )
    return PlannerAgent(story_map, constraint_map)


def test_planner_creates_three_meaningfully_different_candidate_plans() -> None:
    plans = build_planner().plan_all()

    assert [plan.audience_id for plan in plans] == ["family", "young_adult", "dialect_region"]
    assert len({plan.audience_promise for plan in plans}) == 3
    assert len({tuple(segment.scene_id for segment in plan.segments) for plan in plans}) == 3
    assert all(plan.validation is None for plan in plans)
    assert all(any("scene_07" in hypothesis and "excluded" in hypothesis for hypothesis in plan.planning_hypotheses) for plan in plans)


def test_planner_segments_are_source_grounded_and_avoid_known_twist() -> None:
    plans = build_planner().plan_all()

    for plan in plans:
        assert all(segment.evidence[0] == f"scene:{segment.scene_id}" for segment in plan.segments)
        assert all(segment.scene_id != "scene_07" for segment in plan.segments)
        assert all("contract:" in " ".join(segment.evidence) for segment in plan.segments)
