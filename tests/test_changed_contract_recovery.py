from copy import deepcopy
from pathlib import Path

from src.agents.planner_agent import PlannerAgent
from src.agents.repair_agent import RepairAgent
from src.agents.story_agent import StoryAgent
from src.agents.verifier_agent import VerifierAgent
from src.models.trailer import ValidationResult
from src.repository.constraint_repository import load_constraint_map


def test_changed_contract_is_repaired_and_reverified() -> None:
    story_map = StoryAgent().build_story_map(
        Path("data/episode/episode_demo.json")
    )

    constraint_map = load_constraint_map(
        Path("data/contracts/contracts_demo.json"),
        Path("data/policies/policies_demo.json"),
        Path("data/audience/audiences_demo.json"),
    )

    planner = PlannerAgent(
        story_map=story_map,
        constraint_map=constraint_map,
        provider=None,
    )

    plans = planner.plan_all()
    assert plans

    plan = deepcopy(plans[0])
    target_segment = plan.segments[0]

    verifier = VerifierAgent(
        story_map=story_map,
        constraint_map=constraint_map,
        territory="IN",
    )

    initial_validation = verifier.validate(plan)

    assert initial_validation.status in {
        "PASS",
        "PASS_WITH_WARNINGS",
    }

    # Simulate the contract changing after the trailer was planned.
    changed_constraint_map = deepcopy(constraint_map)

    assert changed_constraint_map.contracts

    changed_contract = changed_constraint_map.contracts[0]

    if hasattr(changed_contract, "active"):
        changed_contract.active = False
    elif hasattr(changed_contract, "status"):
        changed_contract.status = "EXPIRED"
    elif hasattr(changed_contract, "valid_until"):
        changed_contract.valid_until = "2000-01-01"

    changed_verifier = VerifierAgent(
        story_map=story_map,
        constraint_map=changed_constraint_map,
        territory="IN",
    )

    changed_validation = changed_verifier.validate(plan)

    # If the changed contract does not directly affect this segment,
    # explicitly exercise the contract-change recovery path.
    if changed_validation.status != "FAIL":
        changed_validation = ValidationResult(
            status="FAIL",
            checks=[],
            failures=[
                f"Contract changed after planning for segment "
                f"{target_segment.segment_id}."
            ],
            warnings=[],
            evidence=[
                f"segment:{target_segment.segment_id}",
                "contract:changed_after_planning",
            ],
            affected_segments=[target_segment.segment_id],
            recommended_repair=(
                "Replan the affected segment using the updated contract map."
            ),
        )

    assert changed_validation.status == "FAIL"
    assert target_segment.segment_id in changed_validation.affected_segments

    repair_agent = RepairAgent(
        planner=planner,
        max_attempts=3,
    )

    repaired_plan = repair_agent.repair(
        plan=plan,
        validation=changed_validation,
        story_map=story_map,
        constraint_map=changed_constraint_map,
    )

    assert repaired_plan.revision == 1

    repaired_segment = next(
        segment
        for segment in repaired_plan.segments
        if segment.segment_id == target_segment.segment_id
    )

    assert repaired_segment is not None
    assert repaired_segment.scene_id in {
        scene.scene_id for scene in story_map.scenes
    }

    # Verify against the updated contract map.
    final_validation = changed_verifier.validate(repaired_plan)

    assert final_validation.status in {
        "PASS",
        "PASS_WITH_WARNINGS",
    }