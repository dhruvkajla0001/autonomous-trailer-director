"""End-to-end checks for the independent deterministic verification pipeline."""

from __future__ import annotations

from src.agents.planner_agent import PlannerAgent
from tests.validation_helpers import verified_context


def test_all_grounded_mock_candidates_pass_deterministic_verification() -> None:
    story, constraints, verifier = verified_context()

    results = [verifier.validate(plan) for plan in PlannerAgent(story, constraints).plan_all()]

    assert [result.status for result in results] == ["PASS", "PASS", "PASS"]


def test_mismatched_evidence_is_rejected() -> None:
    story, constraints, verifier = verified_context()
    plan = PlannerAgent(story, constraints).plan_for_audience("family")
    unsupported_evidence = plan.segments[0].model_copy(update={"evidence": ["scene:scene_999"]})

    result = verifier.validate(plan.model_copy(update={"segments": [unsupported_evidence, *plan.segments[1:]]}))

    assert result.status == "FAIL"
    assert any(check.check_type == "evidence" and check.status == "FAIL" for check in result.checks)
