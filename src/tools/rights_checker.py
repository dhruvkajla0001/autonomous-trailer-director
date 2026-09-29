"""Deterministic contractual-rights checks for selected trailer resources."""

from __future__ import annotations

from datetime import date

from src.models.story import Scene
from src.models.trailer import TrailerSegment, ValidationCheck
from src.tools.constraint_lookup import ConstraintLookup, ConstraintNotFoundError


class RightsChecker:
    """Checks actors and chosen audio against promotional, territory, and expiry terms."""

    def __init__(self, lookup: ConstraintLookup, territory: str, as_of: date | None = None) -> None:
        self._lookup = lookup
        self._territory = territory
        self._as_of = as_of or date.today()

    def check_segment(self, segment: TrailerSegment, scene: Scene) -> ValidationCheck:
        """Return one segment-level result so repair can identify exact dependencies."""
        resources = [*scene.actors, segment.audio]
        failures: list[str] = []
        evidence: list[str] = []
        for resource_id in resources:
            try:
                contract = self._lookup.contract_for(resource_id)
            except ConstraintNotFoundError:
                failures.append(f"No contract exists for {resource_id}.")
                continue
            evidence.extend(contract.evidence)
            if not contract.promotional_use_allowed:
                failures.append(f"Promotional use is not allowed for {resource_id}.")
            if self._territory not in contract.territories:
                failures.append(f"{resource_id} is not licensed for territory {self._territory}.")
            if contract.expires_at is not None and contract.expires_at < self._as_of:
                failures.append(f"Rights for {resource_id} expired on {contract.expires_at.isoformat()}.")

        if failures:
            return ValidationCheck(
                check_id=f"rights:{segment.segment_id}",
                check_type="rights",
                status="FAIL",
                message=" ".join(failures),
                evidence=_deduplicate(evidence),
                affected_segments=[segment.segment_id],
                recommended_repair="Replace the affected audio or scene with a resource that has active promotional rights.",
            )
        return ValidationCheck(
            check_id=f"rights:{segment.segment_id}",
            check_type="rights",
            status="PASS",
            message=f"Actors and selected audio are licensed for {self._territory} promotional use.",
            evidence=_deduplicate(evidence),
            affected_segments=[segment.segment_id],
        )


def _deduplicate(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
