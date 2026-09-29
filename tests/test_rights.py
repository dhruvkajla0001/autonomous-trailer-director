"""A plan must fail when selected audio lacks promotional rights."""

from __future__ import annotations

from tests.validation_helpers import family_plan, verified_context


def test_unlicensed_audio_rejects_the_plan() -> None:
    _, _, verifier = verified_context()
    plan = family_plan()
    unlicensed = plan.segments[0].model_copy(
        update={
            "audio": "track_licensed_uk_only",
            "evidence": [*plan.segments[0].evidence, "contract:track_licensed_uk_only"],
        }
    )
    result = verifier.validate(plan.model_copy(update={"segments": [unlicensed, *plan.segments[1:]]}))

    assert result.status == "FAIL"
    assert any(check.check_type == "rights" and check.status == "FAIL" for check in result.checks)
