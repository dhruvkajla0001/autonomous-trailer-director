"""Audience policy must independently reject unsuitable source content."""

from __future__ import annotations

from tests.validation_helpers import family_plan, verified_context


def test_family_plan_rejects_frightening_scene() -> None:
    _, _, verifier = verified_context()
    plan = family_plan()
    frightening = plan.segments[0].model_copy(
        update={
            "scene_id": "scene_04",
            "video": "scene_04",
            "source_in": "00:00:56.000",
            "source_out": "00:01:02.000",
            "audio": "track_storm_01",
            "subtitle": None,
            "evidence": ["scene:scene_04", "contract:actor_nila", "contract:track_storm_01"],
        }
    )
    result = verifier.validate(plan.model_copy(update={"segments": [frightening, *plan.segments[1:]]}))

    assert result.status == "FAIL"
    assert any(check.check_type == "audience_policy" and check.status == "FAIL" for check in result.checks)
