"""CLI entry point for the Autonomous Trailer Director.

Workflow:

Episode
    -> Story Map
    -> Constraint Map
    -> Audience Planning
    -> Candidate Trailer Plans
    -> Independent Verification
    -> Selective Repair
    -> Re-verification
    -> Final JSON artifacts
    -> Decision log

Hard constraints are enforced by deterministic validators.
The verifier is independent of the planner.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from src.agents.planner_agent import PlannerAgent
from src.agents.repair_agent import RepairAgent
from src.agents.story_agent import StoryAgent
from src.agents.verifier_agent import VerifierAgent
from src.models.trailer import DecisionLog, TrailerPlan, ValidationResult
from src.providers.llm import OllamaProvider
from src.repository.constraint_repository import (
    ConstraintIngestionError,
    load_constraint_map,
)
from src.repository.episode_repository import EpisodeIngestionError


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.pipeline",
        description="Autonomous Trailer Director",
    )

    parser.add_argument(
        "--mode",
        choices=("mock", "llm", "replay"),
        default="mock",
        help=(
            "Execution mode. Mock mode is deterministic and "
            "requires no API key."
        ),
    )

    parser.add_argument(
        "--contracts-path",
        type=Path,
        default=Path("data/contracts/contracts_demo.json"),
    )

    parser.add_argument(
        "--policies-path",
        type=Path,
        default=Path("data/policies/policies_demo.json"),
    )

    parser.add_argument(
        "--audiences-path",
        type=Path,
        default=Path("data/audience/audiences_demo.json"),
    )

    parser.add_argument(
        "--episode-path",
        type=Path,
        default=Path("data/episode/episode_demo.json"),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("sample_run"),
    )

    return parser


# ---------------------------------------------------------------------
# Decision logging
# ---------------------------------------------------------------------


def create_pipeline_decision_log(
    *,
    plan: TrailerPlan,
    validation: ValidationResult,
    provider: str,
    decision: str,
    tool_calls: list[str],
) -> DecisionLog:
    """Create an observability record for one pipeline decision."""

    return DecisionLog(
        timestamp=datetime.now(timezone.utc),
        agent="pipeline",
        decision=decision,
        evidence=[
            reference
            for segment in plan.segments
            for reference in segment.evidence
        ],
        input_summary=(
            f"Story map and constraint map for audience "
            f"{plan.audience_id}."
        ),
        output_summary=plan.audience_promise,
        validation_status=validation.status,
        risk=[],
        provider=provider,
        tool_calls=tool_calls,
        estimated_cost_usd=plan.estimated_cost_usd,
        revision=plan.revision,
        revision_reason=getattr(
            plan,
            "revision_reason",
            None,
        ),
        decision_id=(
            f"pipeline:{plan.trailer_id}:r{plan.revision}"
        ),
        input_references=[],
        output=plan.model_dump(mode="json"),
        confidence=1.0,
        uncertainties=validation.warnings,
    )


def create_repair_decision_log(
    *,
    plan: TrailerPlan,
    validation: ValidationResult,
) -> DecisionLog:
    """Record a selective repair decision."""

    return DecisionLog(
        timestamp=datetime.now(timezone.utc),
        agent="repair_agent",
        decision=(
            f"Repaired affected segments for "
            f"{plan.audience_id} after verification failure."
        ),
        evidence=validation.evidence,
        input_summary=(
            f"Verification failure for {plan.audience_id}; "
            f"affected segments: "
            f"{', '.join(validation.affected_segments)}"
        ),
        output_summary=plan.audience_promise,
        validation_status="REPAIR_REQUIRED",
        risk=[],
        provider="deterministic_mock",
        tool_calls=[
            "verifier_agent",
            "planner_agent.repair",
            "selective_segment_merge",
        ],
        estimated_cost_usd=plan.estimated_cost_usd,
        revision=plan.revision,
        revision_reason=getattr(
            plan,
            "revision_reason",
            None,
        ),
        decision_id=(
            f"repair:{plan.trailer_id}:r{plan.revision}"
        ),
        input_references=[],
        output=plan.model_dump(mode="json"),
        confidence=1.0,
        uncertainties=validation.failures,
    )


# ---------------------------------------------------------------------
# Artifact writing
# ---------------------------------------------------------------------


def write_json(
    path: Path,
    data: object,
) -> None:
    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------
# Verification + repair
# ---------------------------------------------------------------------


def verify_and_repair(
    *,
    plan: TrailerPlan,
    verifier: VerifierAgent,
    repair_agent: RepairAgent,
    story_map,
    constraint_map,
    max_attempts: int = 3,
) -> tuple[TrailerPlan, list[DecisionLog]]:
    """Verify a candidate and selectively repair it when necessary.

    Returns:
        Final plan and all verification/repair decision logs.
    """

    decision_logs: list[DecisionLog] = []

    current_plan = plan

    for attempt in range(max_attempts):
        validation = verifier.validate(current_plan)

        current_plan.validation = validation

        # -------------------------------------------------------------
        # Verification decision
        # -------------------------------------------------------------

        decision_logs.append(
            create_pipeline_decision_log(
                plan=current_plan,
                validation=validation,
                provider=verifier.provider,
                decision=(
                    "Independent verification passed."
                    if validation.status == "PASS"
                    else (
                        "Independent verification completed with warnings."
                        if validation.status == "PASS_WITH_WARNINGS"
                        else "Independent verification failed."
                    )
                ),
                tool_calls=[
                    "verifier_agent",
                    "scene_search",
                    "spoiler_checker",
                    "rights_checker",
                    "policy_checker",
                    "deterministic_validation",
                ],
            )
        )

        # -------------------------------------------------------------
        # Successful verification
        # -------------------------------------------------------------

        if validation.status in {
            "PASS",
            "PASS_WITH_WARNINGS",
        }:
            current_plan.warnings = [
                warning
                for warning in current_plan.warnings
                if "independent verification" not in warning.lower()
            ]

            if validation.status == "PASS_WITH_WARNINGS":
                current_plan.warnings.extend(
                    validation.warnings
                )

            return current_plan, decision_logs

        # -------------------------------------------------------------
        # Cannot repair
        # -------------------------------------------------------------

        if not validation.affected_segments:
            return current_plan, decision_logs

        if attempt >= max_attempts - 1:
            return current_plan, decision_logs

        # -------------------------------------------------------------
        # Selective repair
        # -------------------------------------------------------------

        try:
            repaired_plan = repair_agent.repair(
                plan=current_plan,
                validation=validation,
                story_map=story_map,
                constraint_map=constraint_map,
            )
        except Exception as error:
            current_plan.warnings.append(
                f"Repair failed: {error}"
            )
            return current_plan, decision_logs

        repaired_plan.validation = None

        decision_logs.append(
            create_repair_decision_log(
                plan=repaired_plan,
                validation=validation,
            )
        )

        current_plan = repaired_plan

    return current_plan, decision_logs


# ---------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = build_parser().parse_args(argv)

    # -----------------------------------------------------------------
    # Replay mode
    # -----------------------------------------------------------------

    if args.mode == "replay":
        print(
            "Replay mode is not required for this first executable "
            "workflow."
        )
        print(
            "Use --mode mock or --mode llm. "
            "Mock mode requires no API key and is deterministic."
        )
        return 0

    # -----------------------------------------------------------------
    # Select LLM provider
    # -----------------------------------------------------------------

    provider = None

    if args.mode == "llm":
        provider = OllamaProvider(
        timeout_seconds=180.0)

    # -----------------------------------------------------------------
    # 1. Build story map
    # -----------------------------------------------------------------

    try:
        story_map = StoryAgent(
            provider=provider,
        ).build_story_map(
            args.episode_path
        )

        # -------------------------------------------------------------
        # 2. Build constraint map
        # -------------------------------------------------------------

        constraint_map = load_constraint_map(
            args.contracts_path,
            args.policies_path,
            args.audiences_path,
        )

    except (
        EpisodeIngestionError,
        ConstraintIngestionError,
    ) as error:
        print(
            f"Source ingestion failed: {error}"
        )
        return 2

    # -----------------------------------------------------------------
    # Prepare output directory
    # -----------------------------------------------------------------

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -----------------------------------------------------------------
    # Write source maps
    # -----------------------------------------------------------------

    story_output_path = (
        args.output_dir / "story_map.json"
    )

    constraint_output_path = (
        args.output_dir / "constraint_map.json"
    )

    story_output_path.write_text(
        story_map.model_dump_json(indent=2),
        encoding="utf-8",
    )

    constraint_output_path.write_text(
        constraint_map.model_dump_json(indent=2),
        encoding="utf-8",
    )

    # -----------------------------------------------------------------
    # Header
    # -----------------------------------------------------------------

    print()
    print("=" * 60)
    print("AUTONOMOUS TRAILER DIRECTOR")
    print("=" * 60)

    print()
    print(
        f"Validated story map: PASS "
        f"({len(story_map.scenes)} scenes)"
    )

    print(
        f"Constraint Map  : PASS "
        f"({len(constraint_map.contracts)} contracts, "
        f"{len(constraint_map.constraints)} rules)"
    )

    # -----------------------------------------------------------------
    # 3. Audience planning
    # -----------------------------------------------------------------

    planner = PlannerAgent(
        story_map=story_map,
        constraint_map=constraint_map,
        provider=provider,
    )

    try:
        plans = planner.plan_all()

    except Exception as error:
        print()
        print(
            f"Planning failed: {error}"
        )
        return 3

    # -----------------------------------------------------------------
    # 4. Build independent verifier
    # -----------------------------------------------------------------

    verifier = VerifierAgent(
        story_map=story_map,
        constraint_map=constraint_map,
        territory="IN",
    )

    # -----------------------------------------------------------------
    # 5. Build repair agent
    # -----------------------------------------------------------------

    repair_agent = RepairAgent(
        planner=planner,
        max_attempts=3,
    )

    # -----------------------------------------------------------------
    # 6. Verify, selectively repair, and re-verify
    # -----------------------------------------------------------------

    all_passed = True
    decision_logs: list[DecisionLog] = []

    for plan in plans:

        print()
        print(
            f"{plan.audience_id.replace('_', ' ').title()} Trailer"
        )

        print(
            "  Planning       : PASS"
        )

        try:
            final_plan, logs = verify_and_repair(
                plan=plan,
                verifier=verifier,
                repair_agent=repair_agent,
                story_map=story_map,
                constraint_map=constraint_map,
                max_attempts=3,
            )

        except Exception as error:
            print(
                f"  Verification   : ERROR"
            )
            print(
                f"  Problems       : {error}"
            )
            all_passed = False
            continue

        # -------------------------------------------------------------
        # Store logs
        # -------------------------------------------------------------

        decision_logs.extend(logs)

        # -------------------------------------------------------------
        # Store verifier-agent semantic logs if any
        # -------------------------------------------------------------

        decision_logs.extend(
            verifier.decision_logs
        )

        # -------------------------------------------------------------
        # Final validation
        # -------------------------------------------------------------

        validation = final_plan.validation

        if validation is None:
            print(
                "  Verification   : NOT RUN"
            )
            all_passed = False
            continue

        # -------------------------------------------------------------
        # Remove stale candidate warning after successful verification
        # -------------------------------------------------------------

        if validation.status in {
            "PASS",
            "PASS_WITH_WARNINGS",
        }:
            final_plan.warnings = [
                warning
                for warning in final_plan.warnings
                if "independent verification" not in warning.lower()
            ]

            if validation.status == "PASS_WITH_WARNINGS":
                for warning in validation.warnings:
                    if warning not in final_plan.warnings:
                        final_plan.warnings.append(
                            warning
                        )

        # -------------------------------------------------------------
        # Write final trailer artifact
        # -------------------------------------------------------------

        trailer_filename = (
            f"{final_plan.audience_id}_trailer.json"
        )

        trailer_path = (
            args.output_dir / trailer_filename
        )

        trailer_path.write_text(
            final_plan.model_dump_json(indent=2),
            encoding="utf-8",
        )

        # -------------------------------------------------------------
        # Console output
        # -------------------------------------------------------------

        print(
            f"  Verification   : {validation.status}"
        )

        print(
            f"  Segments       : "
            f"{len(final_plan.segments)}"
        )

        print(
            f"  Duration       : "
            f"{final_plan.duration_seconds:.2f}s"
        )

        print(
            f"  Revision       : "
            f"{final_plan.revision}"
        )

        if validation.failures:
            all_passed = False

            print(
                "  Problems:"
            )

            for failure in validation.failures:
                print(
                    f"    - {failure}"
                )

        elif validation.warnings:
            print(
                "  Warnings:"
            )

            for warning in validation.warnings:
                print(
                    f"    - {warning}"
                )

        else:
            print(
                "  Problems       : None"
            )

        print(
            f"  Output         : {trailer_path}"
        )

    # -----------------------------------------------------------------
    # 7. Write verifier semantic decision records
    # -----------------------------------------------------------------

    # The verifier may have generated semantic decision records.
    # Avoid adding duplicate objects with identical decision IDs.
    unique_logs: dict[str, DecisionLog] = {}

    for log in decision_logs:
        unique_logs[log.decision_id] = log

    # -----------------------------------------------------------------
    # 8. Write decision log
    # -----------------------------------------------------------------

    decision_log_path = (
        args.output_dir / "decision_log.json"
    )

    write_json(
        decision_log_path,
        [
            log.model_dump(mode="json")
            for log in unique_logs.values()
        ],
    )

    # -----------------------------------------------------------------
    # 9. Final status
    # -----------------------------------------------------------------

    print()
    print("=" * 60)

    if all_passed:
        print(
            "FINAL STATUS: PASS"
        )
    else:
        print(
            "FINAL STATUS: REVIEW REQUIRED"
        )

    print("=" * 60)

    print()
    print(
        f"Artifacts written to: "
        f"{args.output_dir}"
    )

    print()
    print("Generated:")
    print(
        "  - story_map.json"
    )
    print(
        "  - constraint_map.json"
    )
    print(
        "  - family_trailer.json"
    )
    print(
        "  - young_adult_trailer.json"
    )
    print(
        "  - dialect_region_trailer.json"
    )
    print(
        "  - decision_log.json"
    )

    return 0 if all_passed else 4


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
