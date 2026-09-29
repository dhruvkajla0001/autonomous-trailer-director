from copy import deepcopy
from pathlib import Path

from src.agents.planner_agent import PlannerAgent
from src.agents.repair_agent import RepairAgent
from src.agents.story_agent import StoryAgent
from src.agents.verifier_agent import VerifierAgent
from src.models.trailer import ValidationResult
from src.repository.constraint_repository import load_constraint_map


def test_expired_music_rights_are_repaired_and_reverified():
    # -------------------------------------------------------------
    # 1. Load source-of-truth data
    # -------------------------------------------------------------

    story_map = StoryAgent().build_story_map(
        Path("data/episode/episode_demo.json")
    )

    constraint_map = load_constraint_map(
        Path("data/contracts/contracts_demo.json"),
        Path("data/policies/policies_demo.json"),
        Path("data/audience/audiences_demo.json"),
    )

    # -------------------------------------------------------------
    # 2. Create planner and generate a normal trailer
    # -------------------------------------------------------------

    planner = PlannerAgent(
        story_map=story_map,
        constraint_map=constraint_map,
        provider=None,
    )

    plans = planner.plan_all()

    assert plans

    plan = deepcopy(plans[0])

    # -------------------------------------------------------------
    # 3. Find a segment containing audio
    # -------------------------------------------------------------

    music_segment = None

    for segment in plan.segments:
        if getattr(segment, "audio", None):
            music_segment = segment
            break

    assert music_segment is not None, (
        "Demo trailer contains no audio-bearing segment "
        "for the rights recovery scenario."
    )

    assert music_segment.audio is not None

    # -------------------------------------------------------------
    # 4. Create independent verifier
    # -------------------------------------------------------------

    verifier = VerifierAgent(
        story_map=story_map,
        constraint_map=constraint_map,
        territory="IN",
    )

    # -------------------------------------------------------------
    # 5. Confirm the original plan is valid
    # -------------------------------------------------------------

    initial_validation = verifier.validate(plan)

    assert initial_validation.status in {
        "PASS",
        "PASS_WITH_WARNINGS",
    }

    # -------------------------------------------------------------
    # 6. Simulate an expired music-rights failure
    #
    # This uses the real ValidationResult model and the same
    # structure produced by the verifier.
    # -------------------------------------------------------------

    rights_failure = ValidationResult(
        status="FAIL",
        checks=[],
        failures=[
            (
                f"Music rights expired for segment "
                f"{music_segment.segment_id}."
            )
        ],
        warnings=[],
        evidence=[
            f"segment:{music_segment.segment_id}",
            "rights:expired",
        ],
        affected_segments=[
            music_segment.segment_id
        ],
        recommended_repair=(
            "Replace the expired music with an approved "
            "rights-cleared audio option."
        ),
    )

    # -------------------------------------------------------------
    # 7. Verify that this is actually treated as a failure
    # -------------------------------------------------------------

    assert rights_failure.status == "FAIL"

    assert (
        music_segment.segment_id
        in rights_failure.affected_segments
    )

    # -------------------------------------------------------------
    # 8. Run RepairAgent
    # -------------------------------------------------------------

    repair_agent = RepairAgent(
        planner=planner,
        max_attempts=3,
    )

    repaired_plan = repair_agent.repair(
        plan=plan,
        validation=rights_failure,
        story_map=story_map,
        constraint_map=constraint_map,
    )

    # -------------------------------------------------------------
    # 9. Repair must create revision 1
    # -------------------------------------------------------------

    assert repaired_plan.revision == 1

    # -------------------------------------------------------------
    # 10. The affected segment must still exist
    # -------------------------------------------------------------

    repaired_segment = next(
        (
            segment
            for segment in repaired_plan.segments
            if segment.segment_id
            == music_segment.segment_id
        ),
        None,
    )

    assert repaired_segment is not None

    # -------------------------------------------------------------
    # 11. Re-verify the repaired plan
    # -------------------------------------------------------------

    repaired_validation = verifier.validate(
        repaired_plan
    )

    assert repaired_validation.status in {
        "PASS",
        "PASS_WITH_WARNINGS",
    }