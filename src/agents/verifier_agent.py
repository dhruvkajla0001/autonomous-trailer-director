"""Independent deterministic verification of candidate trailer edit plans."""

from __future__ import annotations

from datetime import date, datetime, timezone

from pydantic import ValidationError

from src.models.constraints import ConstraintMap
from src.models.story import DialogueLine, Scene, StoryMap, timecode_to_milliseconds
from src.models.trailer import DecisionLog, SemanticReview, TrailerPlan, TrailerSegment, ValidationCheck, ValidationResult
from src.providers.base import GenerationRequest, GenerationResponse, LLMProvider, LLMProviderError
from src.tools.constraint_lookup import ConstraintLookup, ConstraintNotFoundError
from src.tools.policy_checker import PolicyChecker
from src.tools.rights_checker import RightsChecker
from src.tools.scene_search import SceneNotFoundError, SceneSearch
from src.tools.spoiler_checker import SpoilerChecker


class VerifierAgent:
    """Combines independent deterministic checks; it never imports the planner."""

    agent_name = "verifier_agent"
    provider = "deterministic_rules"

    def __init__(
        self,
        story_map: StoryMap,
        constraint_map: ConstraintMap,
        territory: str = "IN",
        as_of: date | None = None,
        semantic_provider: LLMProvider | None = None,
    ) -> None:
        lookup = ConstraintLookup(constraint_map)
        self._story_map = story_map
        self._scene_search = SceneSearch(story_map)
        self._lookup = lookup
        self._spoilers = SpoilerChecker(story_map)
        self._rights = RightsChecker(lookup, territory=territory, as_of=as_of)
        self._policy = PolicyChecker(story_map, lookup)
        self._semantic_provider = semantic_provider
        self._decision_logs: list[DecisionLog] = []

    @property
    def decision_logs(self) -> list[DecisionLog]:
        """Return semantic-verification provider-call records without secrets."""
        return list(self._decision_logs)

    def validate(self, plan: TrailerPlan) -> ValidationResult:
        """Return a complete, reject-capable validation record for one candidate plan."""
        checks: list[ValidationCheck] = []
        try:
            self._lookup.audience(plan.audience_id)
        except ConstraintNotFoundError as error:
            checks.append(_failure("audience", "audience", str(error), []))
            return _result(checks)

        for segment in plan.segments:
            scene, source_checks = self._source_checks(segment)
            checks.extend(source_checks)
            if scene is None:
                continue
            checks.extend(self._evidence_checks(segment, scene.dialogue))
            checks.append(self._spoilers.check_segment(segment))
            checks.append(self._rights.check_segment(segment, scene))
            checks.extend(self._policy.check_segment(plan, segment, scene))

        checks.extend(self._policy.check_plan(plan))
        checks.append(self._budget_check(plan))
        checks.append(self._duration_check(plan))
        deterministic_result = _result(checks)
        if deterministic_result.status == "FAIL" or self._semantic_provider is None:
            return deterministic_result
        return self._apply_semantic_review(plan, deterministic_result)

    def _apply_semantic_review(self, plan: TrailerPlan, deterministic_result: ValidationResult) -> ValidationResult:
        response = self._semantic_provider.generate(self._semantic_request(plan, deterministic_result))
        try:
            review = SemanticReview.model_validate(response.output)
        except ValidationError as error:
            raise LLMProviderError("Semantic verifier response failed its strict schema") from error
        self._validate_semantic_review(review, plan, deterministic_result)
        semantic_check = ValidationCheck(
            check_id=f"semantic:{plan.trailer_id}",
            check_type="semantic_verification",
            status="PASS" if review.status == "PASS" else "WARN" if review.status == "PASS_WITH_WARNINGS" else "FAIL",
            message=review.explanation,
            evidence=review.evidence,
            affected_segments=review.affected_segments,
            recommended_repair=review.recommended_repair,
        )
        combined = _result([*deterministic_result.checks, semantic_check]).model_copy(
            update={"risk_flags": review.risk_flags}
        )
        self._record_semantic_response(response, plan, review, combined)
        return combined

    def _semantic_request(self, plan: TrailerPlan, deterministic_result: ValidationResult) -> GenerationRequest:
        return GenerationRequest(
            request_id=f"semantic:{plan.trailer_id}:r{plan.revision}",
            purpose="semantic_verification",
            system_instruction=(
                "You are an independent trailer verifier, not the planner. Challenge the plan for misleading narrative implication, "
                "unsupported claims, accidental spoilers, promise mismatch, cultural stereotyping, unsafe framing, and misuse of engagement data. "
                "Deterministic validation is authoritative: never override a failure. Return JSON with status, explanation, risk_flags, evidence, "
                "affected_segments, and recommended_repair."
            ),
            untrusted_data={
                "story_map": self._story_map.model_dump(),
                "trailer_plan": plan.model_dump(),
                "deterministic_validation": deterministic_result.model_dump(),
            },
        )

    @staticmethod
    def _validate_semantic_review(review: SemanticReview, plan: TrailerPlan, deterministic_result: ValidationResult) -> None:
        known_evidence = {reference for segment in plan.segments for reference in segment.evidence}
        known_evidence.update(deterministic_result.evidence)
        submitted_evidence = [*review.evidence, *(reference for flag in review.risk_flags for reference in flag.evidence)]
        unsupported = sorted({reference for reference in submitted_evidence if reference not in known_evidence})
        if unsupported:
            raise LLMProviderError(f"Semantic verifier cited unsupported evidence: {', '.join(unsupported)}")
        known_segment_ids = {segment.segment_id for segment in plan.segments}
        unknown_segments = sorted(set(review.affected_segments) - known_segment_ids)
        if unknown_segments:
            raise LLMProviderError(f"Semantic verifier cited unknown segment IDs: {', '.join(unknown_segments)}")

    def _record_semantic_response(
        self,
        response: GenerationResponse,
        plan: TrailerPlan,
        review: SemanticReview,
        result: ValidationResult,
    ) -> None:
        self._decision_logs.append(
            DecisionLog(
                timestamp=datetime.now(timezone.utc),
                agent=self.agent_name,
                decision="Independent LLM semantic review accepted after grounding checks.",
                evidence=review.evidence,
                input_summary="Canonical story, plan, constraint-derived deterministic checks, supplied as untrusted data.",
                output_summary=review.explanation,
                validation_status=result.status,
                risk=review.risk_flags,
                provider=response.provider,
                tool_calls=["deterministic_validation", "semantic_evidence_validation"],
                estimated_cost_usd=response.estimated_cost_usd,
                revision=plan.revision,
                decision_id=response.request_id,
                input_references=self._story_map.source_refs,
                output=response.output,
                uncertainties=[flag.message for flag in review.risk_flags if flag.severity == "warning"],
            )
        )

    def _source_checks(self, segment: TrailerSegment) -> tuple[Scene | None, list[ValidationCheck]]:
        try:
            scene = self._scene_search.get_by_id(segment.scene_id)
        except SceneNotFoundError as error:
            return None, [_failure(f"scene:{segment.segment_id}", "scene_existence", str(error), [segment.segment_id])]

        checks = [
            ValidationCheck(
                check_id=f"scene:{segment.segment_id}",
                check_type="scene_existence",
                status="PASS",
                message="Selected scene exists in the supplied episode package.",
                evidence=[f"scene:{scene.scene_id}"],
                affected_segments=[segment.segment_id],
            )
        ]
        segment_start = timecode_to_milliseconds(segment.source_in)
        segment_end = timecode_to_milliseconds(segment.source_out)
        scene_start = timecode_to_milliseconds(scene.source_in)
        scene_end = timecode_to_milliseconds(scene.source_out)
        range_is_valid = scene_start <= segment_start < segment_end <= scene_end
        video_is_valid = segment.video == scene.scene_id
        checks.append(
            ValidationCheck(
                check_id=f"source_range:{segment.segment_id}",
                check_type="source_accuracy",
                status="PASS" if range_is_valid and video_is_valid else "FAIL",
                message=(
                    "Segment timecodes and video reference are grounded in the selected scene."
                    if range_is_valid and video_is_valid
                    else "Segment timecodes or video reference are not grounded in the selected scene."
                ),
                evidence=[f"scene:{scene.scene_id}"],
                affected_segments=[segment.segment_id],
                recommended_repair="Use the scene's supplied ID and an in-range source timecode." if not (range_is_valid and video_is_valid) else None,
            )
        )
        return scene, checks

    def _evidence_checks(self, segment: TrailerSegment, dialogue: list[DialogueLine]) -> list[ValidationCheck]:
        known_dialogue_ids = {item.dialogue_id for item in dialogue}
        known_contract_evidence = self._lookup.contract_evidence_references()
        failures: list[str] = []
        for reference in segment.evidence:
            prefix, _, identifier = reference.partition(":")
            if prefix == "scene" and identifier != segment.scene_id:
                failures.append(f"Evidence {reference} does not match selected scene.")
            elif prefix == "dialogue" and identifier not in known_dialogue_ids:
                failures.append(f"Evidence {reference} is not dialogue in the selected scene.")
            elif prefix == "contract" and reference not in known_contract_evidence:
                failures.append(f"Evidence {reference} is not an approved contract reference.")
            elif prefix not in {"scene", "dialogue", "contract"}:
                failures.append(f"Evidence reference has unsupported type: {reference}.")
        return [
            ValidationCheck(
                check_id=f"evidence:{segment.segment_id}",
                check_type="evidence",
                status="FAIL" if failures else "PASS",
                message=" ".join(failures) if failures else "All segment evidence references resolve to approved source records.",
                evidence=segment.evidence,
                affected_segments=[segment.segment_id],
                recommended_repair="Replace unsupported evidence with canonical scene, dialogue, or contract references." if failures else None,
            )
        ]

    def _budget_check(self, plan: TrailerPlan) -> ValidationCheck:
        budget = self._lookup.budget
        within_budget = plan.estimated_cost_usd <= budget.max_total_cost_usd
        return ValidationCheck(
            check_id=f"budget:{plan.trailer_id}",
            check_type="budget",
            status="PASS" if within_budget else "FAIL",
            message=(
                f"Estimated cost ${plan.estimated_cost_usd:.2f} is within the ${budget.max_total_cost_usd:.2f} budget."
                if within_budget
                else f"Estimated cost ${plan.estimated_cost_usd:.2f} exceeds the ${budget.max_total_cost_usd:.2f} budget."
            ),
            evidence=budget.evidence,
            recommended_repair="Use the documented lower-cost fallback plan." if not within_budget else None,
        )

    @staticmethod
    def _duration_check(plan: TrailerPlan) -> ValidationCheck:
        actual_duration = sum(
            (timecode_to_milliseconds(segment.source_out) - timecode_to_milliseconds(segment.source_in)) / 1000
            for segment in plan.segments
        )
        matches = abs(plan.duration_seconds - actual_duration) < 0.001
        return ValidationCheck(
            check_id=f"duration:{plan.trailer_id}",
            check_type="timing",
            status="PASS" if matches else "FAIL",
            message="Declared duration matches source clip durations." if matches else "Declared duration does not match source clip durations.",
            evidence=[f"trailer:{plan.trailer_id}"],
            recommended_repair="Recalculate duration from selected source ranges." if not matches else None,
        )


def _failure(check_id: str, check_type: str, message: str, affected_segments: list[str]) -> ValidationCheck:
    return ValidationCheck(
        check_id=check_id,
        check_type=check_type,
        status="FAIL",
        message=message,
        affected_segments=affected_segments,
        recommended_repair="Replace or correct the unsupported decision before approval.",
    )


def _result(checks: list[ValidationCheck]) -> ValidationResult:
    failures = [check.message for check in checks if check.status == "FAIL"]
    warnings = [check.message for check in checks if check.status == "WARN"]
    affected_segments = list(dict.fromkeys(segment for check in checks for segment in check.affected_segments))
    status = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    repairs = [check.recommended_repair for check in checks if check.recommended_repair]
    return ValidationResult(
        status=status,
        checks=checks,
        failures=failures,
        warnings=warnings,
        evidence=list(dict.fromkeys(reference for check in checks for reference in check.evidence)),
        affected_segments=affected_segments,
        recommended_repair=" ".join(dict.fromkeys(repairs)) or None,
    )
