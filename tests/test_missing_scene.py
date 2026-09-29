"""A hallucinated scene reference must fail before any editorial approval."""

from __future__ import annotations

from tests.validation_helpers import family_plan, verified_context


def test_hallucinated_scene_is_rejected() -> None:
    _, _, verifier = verified_context()
    plan = family_plan()
    hallucinated = plan.segments[0].model_copy(
        update={"scene_id": "scene_404", "video": "scene_404", "evidence": ["scene:scene_404"]}
    )
    result = verifier.validate(plan.model_copy(update={"segments": [hallucinated, *plan.segments[1:]]}))

    assert result.status == "FAIL"
    assert any(check.check_type == "scene_existence" and check.status == "FAIL" for check in result.checks)
