"""Deterministic audience-safety, cultural-respect, and accessibility checks."""

from __future__ import annotations

from src.models.story import Scene, StoryMap, timecode_to_milliseconds
from src.models.trailer import TrailerPlan, TrailerSegment, ValidationCheck
from src.tools.constraint_lookup import ConstraintLookup


class PolicyChecker:
    """Applies structured policy rules; it does not infer demographic stereotypes."""

    def __init__(self, story_map: StoryMap, lookup: ConstraintLookup) -> None:
        self._story_map = story_map
        self._lookup = lookup

    def check_segment(self, plan: TrailerPlan, segment: TrailerSegment, scene: Scene) -> list[ValidationCheck]:
        """Check segment-level rating, cultural, and subtitle requirements."""
        audience = self._lookup.audience(plan.audience_id)
        prohibited_tags = set(audience.prohibited_tags)
        evidence = list(audience.evidence)
        for constraint in self._lookup.constraints_for(plan.audience_id):
            prohibited_tags.update(constraint.prohibited_tags)
            evidence.extend(constraint.evidence)

        matched_tags = sorted(prohibited_tags.intersection(scene.tags))
        policy_check = ValidationCheck(
            check_id=f"policy:{segment.segment_id}",
            check_type="audience_policy",
            status="FAIL" if matched_tags else "PASS",
            message=(
                f"Scene has prohibited tags for {plan.audience_id}: {', '.join(matched_tags)}."
                if matched_tags
                else "Scene complies with the configured audience tag restrictions."
            ),
            evidence=_deduplicate([f"scene:{scene.scene_id}", *evidence]),
            affected_segments=[segment.segment_id],
            recommended_repair="Replace this scene with one that does not carry the prohibited tag(s)." if matched_tags else None,
        )

        has_spoken_content = any(_overlaps(segment, line.source_in, line.source_out) for line in scene.dialogue)
        accessible = not has_spoken_content or bool(segment.subtitle and segment.subtitle.strip())
        accessibility_check = ValidationCheck(
            check_id=f"accessibility:{segment.segment_id}",
            check_type="accessibility",
            status="PASS" if accessible else "FAIL",
            message="Spoken content has a readable subtitle." if accessible else "Spoken content requires a subtitle or equivalent text treatment.",
            evidence=[f"scene:{scene.scene_id}"],
            affected_segments=[segment.segment_id],
            recommended_repair="Add a source-grounded readable subtitle." if not accessible else None,
        )
        return [policy_check, accessibility_check]

    def check_plan(self, plan: TrailerPlan) -> list[ValidationCheck]:
        """Apply whole-plan requirements that cannot be assessed one segment at a time."""
        audience = self._lookup.audience(plan.audience_id)
        selected_scenes = {segment.scene_id for segment in plan.segments}
        selected_tags = {
            tag
            for scene in self._story_map.scenes
            if scene.scene_id in selected_scenes
            for tag in scene.tags
        }
        required_tags = {
            tag
            for constraint in self._lookup.constraints_for(plan.audience_id)
            for tag in constraint.required_tags
        }
        missing_tags = sorted(required_tags - selected_tags)
        cultural_status = "FAIL" if missing_tags else "PASS"
        cultural_message = (
            f"Plan is missing required evidence-based cultural tag(s): {', '.join(missing_tags)}."
            if missing_tags
            else "Plan satisfies configured cultural-context requirements without demographic inference."
        )
        return [
            ValidationCheck(
                check_id=f"cultural:{plan.trailer_id}",
                check_type="cultural_respect",
                status=cultural_status,
                message=cultural_message,
                evidence=[*audience.evidence, *[f"scene:{scene_id}" for scene_id in sorted(selected_scenes)]],
                affected_segments=[segment.segment_id for segment in plan.segments] if missing_tags else [],
                recommended_repair="Select an authentic story-grounded cultural moment; do not add a stereotype." if missing_tags else None,
            )
        ]


def _overlaps(segment: TrailerSegment, source_in: str, source_out: str) -> bool:
    return (
        timecode_to_milliseconds(segment.source_in) < timecode_to_milliseconds(source_out)
        and timecode_to_milliseconds(source_in) < timecode_to_milliseconds(segment.source_out)
    )


def _deduplicate(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
