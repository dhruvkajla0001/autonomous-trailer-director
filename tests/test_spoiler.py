"""A deterministic spoiler rule must reject a compelling but protected clip."""

from __future__ import annotations

from tests.validation_helpers import family_plan, verified_context


def test_protected_spoiler_scene_rejects_the_plan() -> None:
    _, _, verifier = verified_context()
    plan = family_plan()
    protected = plan.segments[0].model_copy(
        update={
            "scene_id": "scene_07",
            "video": "scene_07",
            "source_in": "00:01:58.000",
            "source_out": "00:02:01.000",
            "audio": "track_licensed_uk_only",
            "subtitle": "Dad? You are alive.",
            "evidence": ["scene:scene_07", "dialogue:dialogue_07_01", "contract:actor_nila", "contract:track_licensed_uk_only"],
        }
    )
    result = verifier.validate(plan.model_copy(update={"segments": [protected, *plan.segments[1:]]}))

    assert result.status == "FAIL"
    assert any(check.check_type == "spoiler" and check.status == "FAIL" for check in result.checks)
