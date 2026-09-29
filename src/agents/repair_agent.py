"""Selective repair agent for invalid trailer plans."""

from __future__ import annotations

from src.agents.planner_agent import PlannerAgent
from src.models.trailer import TrailerPlan, ValidationResult


class RepairAgent:
    """Repairs only the segments identified by independent verification."""

    def __init__(
        self,
        planner: PlannerAgent,
        max_attempts: int = 3,
    ) -> None:
        self.planner = planner
        self.max_attempts = max_attempts

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    def repair(
        self,
        *,
        plan: TrailerPlan,
        validation: ValidationResult,
        story_map,
        constraint_map,
    ) -> TrailerPlan:
        """Repair a failed trailer plan.

        The verifier is authoritative. Only segments explicitly
        identified as affected are eligible for replacement.
        """

        # -------------------------------------------------------------
        # Already valid: nothing to repair
        # -------------------------------------------------------------

        if validation.status in {
            "PASS",
            "PASS_WITH_WARNINGS",
        }:
            return plan

        # -------------------------------------------------------------
        # Determine affected segments
        # -------------------------------------------------------------

        affected_segments = self._get_affected_segments(
            validation
        )

        if not affected_segments:
            raise ValueError(
                "Verification failed but no affected segments "
                "were identified."
            )

        # -------------------------------------------------------------
        # Create next revision
        # -------------------------------------------------------------

        next_revision = plan.revision + 1

        repaired_plan = plan.model_copy(
            deep=True
        )

        repaired_plan.revision = next_revision

        # -------------------------------------------------------------
        # Ask planner for targeted repair
        # -------------------------------------------------------------

        repaired_candidate = self.planner.repair(
            plan=repaired_plan,
            validation=validation,
            affected_segment_ids=affected_segments,
            story_map=story_map,
            constraint_map=constraint_map,
        )

        # -------------------------------------------------------------
        # Preserve unaffected segments
        # -------------------------------------------------------------

        merged_plan = self._merge_repair(
            original_plan=plan,
            repaired_plan=repaired_candidate,
            affected_segments=affected_segments,
        )

        # -------------------------------------------------------------
        # New revision requires fresh verification
        # -------------------------------------------------------------

        merged_plan.validation = None

        return merged_plan

    # -----------------------------------------------------------------
    # Affected segments
    # -----------------------------------------------------------------

    @staticmethod
    def _get_affected_segments(
        validation: ValidationResult,
    ) -> list[str]:
        """Extract affected segment IDs from ValidationResult."""

        # Primary source: ValidationResult.affected_segments
        direct_segments = list(
            getattr(
                validation,
                "affected_segments",
                [],
            )
            or []
        )

        if direct_segments:
            return list(
                dict.fromkeys(direct_segments)
            )

        # Compatibility fallback: inspect failed checks.
        affected: list[str] = []

        for check in getattr(
            validation,
            "checks",
            [],
        ):
            if getattr(
                check,
                "status",
                None,
            ) != "FAIL":
                continue

            for segment_id in getattr(
                check,
                "affected_segments",
                [],
            ):
                if segment_id not in affected:
                    affected.append(segment_id)

        return affected

    # -----------------------------------------------------------------
    # Repair reason
    # -----------------------------------------------------------------

    @staticmethod
    def _build_revision_reason(
        validation: ValidationResult,
    ) -> str:
        """Create an auditable explanation for the repair."""

        failures = list(
            getattr(
                validation,
                "failures",
                [],
            )
            or []
        )

        if failures:
            return " | ".join(
                str(failure)
                for failure in failures
            )

        recommended_repair = getattr(
            validation,
            "recommended_repair",
            None,
        )

        if recommended_repair:
            return str(
                recommended_repair
            )

        failed_checks: list[str] = []

        for check in getattr(
            validation,
            "checks",
            [],
        ):
            if getattr(
                check,
                "status",
                None,
            ) != "FAIL":
                continue

            message = getattr(
                check,
                "message",
                None,
            )

            if message:
                failed_checks.append(
                    str(message)
                )

        if failed_checks:
            return " | ".join(
                failed_checks
            )

        return (
            "Repair required after independent verification."
        )

    # -----------------------------------------------------------------
    # Merge
    # -----------------------------------------------------------------

    @staticmethod
    def _merge_repair(
        *,
        original_plan: TrailerPlan,
        repaired_plan: TrailerPlan,
        affected_segments: list[str],
    ) -> TrailerPlan:
        """Replace only affected segments.

        Unaffected segments from the original candidate are preserved.
        """

        affected = set(
            affected_segments
        )

        repaired_by_id = {
            segment.segment_id: segment
            for segment in repaired_plan.segments
        }

        merged_segments = []

        for original_segment in original_plan.segments:
            segment_id = original_segment.segment_id

            if segment_id in affected:
                replacement = repaired_by_id.get(
                    segment_id
                )

                if replacement is None:
                    raise ValueError(
                        "Repair planner did not return a "
                        f"replacement for affected segment "
                        f"{segment_id}."
                    )

                merged_segments.append(
                    replacement
                )

            else:
                # Critical recovery property:
                # preserve the unaffected original segment.
                merged_segments.append(
                    original_segment
                )

        merged_plan = repaired_plan.model_copy(
            deep=True
        )

        merged_plan.segments = merged_segments
        merged_plan.validation = None

        return merged_plan