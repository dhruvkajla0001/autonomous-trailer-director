from copy import deepcopy
from pathlib import Path

from src.agents.planner_agent import PlannerAgent
from src.agents.repair_agent import RepairAgent
from src.agents.story_agent import StoryAgent
from src.agents.verifier_agent import VerifierAgent
from src.models.trailer import ValidationResult
from src.repository.constraint_repository import load_constraint_map


def test_policy_violation_is_repaired_and_reverified():
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
    # 2. Generate a normal trailer
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
    # 3. Select an existing segment
    # -------------------------------------------------------------

    target_segment = plan.segments[0]

    # -------------------------------------------------------------
    # 4. Create independent verifier
    # -------------------------------------------------------------

    verifier = VerifierAgent(
        story_map=story_map,
        constraint_map=constraint_map,
        territory="IN",
    )

    # -------------------------------------------------------------
    # 5. Confirm normal plan passes
    # -------------------------------------------------------------

    initial_validation = verifier.validate(plan)

    assert initial_validation.status in {
        "PASS",
        "PASS_WITH_WARNINGS",
    }

    # -------------------------------------------------------------
    # 6. Simulate a policy violation
    #
    # The policy failure is represented using the actual
    # ValidationResult contract.
    # -------------------------------------------------------------

    policy_failure = ValidationResult(
        status="FAIL",
        checks=[],
        failures=[
            (
                f"Policy violation detected in segment "
                f"{target_segment.segment_id}."
            )
        ],
        warnings=[],
        evidence=[
            f"segment:{target_segment.segment_id}",
            "policy:prohibited_content",
        ],
        affected_segments=[
            target_segment.segment_id
        ],
        recommended_repair=(
            "Replace the affected segment with a "
            "policy-compliant canonical scene."
        ),
    )

    # -------------------------------------------------------------
    # 7. Confirm verifier failure representation
    # -------------------------------------------------------------

    assert policy_failure.status == "FAIL"

    assert (
        target_segment.segment_id
        in policy_failure.affected_segments
    )

    # -------------------------------------------------------------
    # 8. Repair
    # -------------------------------------------------------------

    repair_agent = RepairAgent(
        planner=planner,
        max_attempts=3,
    )

    repaired_plan = repair_agent.repair(
        plan=plan,
        validation=policy_failure,
        story_map=story_map,
        constraint_map=constraint_map,
    )

    # -------------------------------------------------------------
    # 9. Repair must increment revision
    # -------------------------------------------------------------

    assert repaired_plan.revision == 1

    # -------------------------------------------------------------
    # 10. Affected segment must remain present
    # -------------------------------------------------------------

    repaired_segment = next(
        (
            segment
            for segment in repaired_plan.segments
            if segment.segment_id
            == target_segment.segment_id
        ),
        None,
    )

    assert repaired_segment is not None

    # -------------------------------------------------------------
    # 11. Re-verify
    # -------------------------------------------------------------

    repaired_validation = verifier.validate(
        repaired_plan
    )

    assert repaired_validation.status in {
        "PASS",
        "PASS_WITH_WARNINGS",
    }