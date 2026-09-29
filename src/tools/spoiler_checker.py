"""Deterministic spoiler checks grounded in the protected story map."""

from __future__ import annotations

from src.models.story import StoryMap
from src.models.trailer import TrailerSegment, ValidationCheck


class SpoilerChecker:
    """Rejects clips from scenes explicitly marked as protected story facts."""

    def __init__(self, story_map: StoryMap) -> None:
        self._spoilers = tuple(story_map.spoilers)

    def check_segment(self, segment: TrailerSegment) -> ValidationCheck:
        """Fail closed when a selected scene is tied to a protected spoiler fact."""
        matched = [spoiler for spoiler in self._spoilers if segment.scene_id in spoiler.scene_ids]
        if not matched:
            return ValidationCheck(
                check_id=f"spoiler:{segment.segment_id}",
                check_type="spoiler",
                status="PASS",
                message="No protected spoiler fact is referenced by this segment.",
                evidence=[f"scene:{segment.scene_id}"],
                affected_segments=[segment.segment_id],
            )

        evidence = [f"spoiler:{spoiler.spoiler_id}" for spoiler in matched]
        evidence.extend(reference for spoiler in matched for reference in spoiler.source_refs)
        return ValidationCheck(
            check_id=f"spoiler:{segment.segment_id}",
            check_type="spoiler",
            status="FAIL",
            message="Selected source scene contains a protected story fact.",
            evidence=evidence,
            affected_segments=[segment.segment_id],
            recommended_repair="Replace the segment with a non-protected scene; do not trim around a known reveal without editorial review.",
        )
