from copy import deepcopy
from pathlib import Path

from src.agents.planner_agent import PlannerAgent
from src.agents.repair_agent import RepairAgent
from src.agents.story_agent import StoryAgent
from src.agents.verifier_agent import VerifierAgent
from src.repository.constraint_repository import load_constraint_map


def test_invalid_scene_is_repaired_and_reverified():
    # -------------------------------------------------------------
    # 1. Load source-of-truth story and constraints
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
    # 2. Create normal planner
    # -------------------------------------------------------------

    planner = PlannerAgent(
        story_map=story_map,
        constraint_map=constraint_map,
        provider=None,
    )

    plans = planner.plan_all()

    assert plans

    # -------------------------------------------------------------
    # 3. Deliberately corrupt one valid plan
    # -------------------------------------------------------------

    plan = deepcopy(plans[0])

    original_scene_id = plan.segments[0].scene_id

    plan.segments[0].scene_id = "scene_DOES_NOT_EXIST"

    # -------------------------------------------------------------
    # 4. Independent verifier must detect the corruption
    # -------------------------------------------------------------

    verifier = VerifierAgent(
        story_map=story_map,
        constraint_map=constraint_map,
        territory="IN",
    )

    failed_validation = verifier.validate(plan)

    assert failed_validation.status == "FAIL"

    assert failed_validation.affected_segments

    assert plan.segments[0].segment_id in (
        failed_validation.affected_segments
    )

    # -------------------------------------------------------------
    # 5. Repair the affected segment
    # -------------------------------------------------------------

    repair_agent = RepairAgent(
        planner=planner,
        max_attempts=3,
    )

    repaired_plan = repair_agent.repair(
        plan=plan,
        validation=failed_validation,
        story_map=story_map,
        constraint_map=constraint_map,
    )

    # -------------------------------------------------------------
    # 6. Repair must create a new revision
    # -------------------------------------------------------------

    assert repaired_plan.revision == 1

    # The nonexistent scene must no longer be present.
    assert all(
        segment.scene_id != "scene_DOES_NOT_EXIST"
        for segment in repaired_plan.segments
    )

    # The repaired plan must still contain the affected segment.
    assert any(
        segment.segment_id == plan.segments[0].segment_id
        for segment in repaired_plan.segments
    )

    # -------------------------------------------------------------
    # 7. Re-verify the repaired plan
    # -------------------------------------------------------------

    repaired_validation = verifier.validate(
        repaired_plan
    )

    assert repaired_validation.status in {
        "PASS",
        "PASS_WITH_WARNINGS",
    }

    # -------------------------------------------------------------
    # 8. Confirm the original valid scene was not invented
    # -------------------------------------------------------------

    assert repaired_plan.segments[0].scene_id != "scene_DOES_NOT_EXIST"

    # This is intentionally informational rather than a strict
    # equality assertion because the repair agent is allowed to
    # choose another valid canonical scene.
    assert (
        repaired_plan.segments[0].scene_id
        in {scene.scene_id for scene in story_map.scenes}
    )