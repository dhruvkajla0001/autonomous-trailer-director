"""Read-only deterministic access to independently loaded constraint memory."""

from __future__ import annotations

from src.models.constraints import AudienceProfile, BudgetConfig, Constraint, ConstraintMap, Contract, HistoricPerformanceRecord


class ConstraintNotFoundError(LookupError):
    """Raised when a decision attempts to use unknown rights or audience data."""


class ConstraintLookup:
    """Provides source-of-truth lookups without making policy decisions itself."""

    def __init__(self, constraint_map: ConstraintMap) -> None:
        self._constraint_map = constraint_map
        self._contracts = {contract.resource_id: contract for contract in constraint_map.contracts}
        self._audiences = {audience.audience_id: audience for audience in constraint_map.audiences}

    @property
    def budget(self) -> BudgetConfig:
        """Return the configured shared processing budget."""
        return self._constraint_map.budget

    @property
    def historic_performance(self) -> list[HistoricPerformanceRecord]:
        """Return retrospective metrics as non-authoritative planning inputs."""
        return list(self._constraint_map.historic_performance)

    def contract_for(self, resource_id: str) -> Contract:
        """Return the governing contract or fail closed when rights are unknown."""
        try:
            return self._contracts[resource_id]
        except KeyError as error:
            raise ConstraintNotFoundError(f"No contract exists for resource: {resource_id}") from error

    def audience(self, audience_id: str) -> AudienceProfile:
        """Return an approved audience profile."""
        try:
            return self._audiences[audience_id]
        except KeyError as error:
            raise ConstraintNotFoundError(f"Unknown audience profile: {audience_id}") from error

    def constraints_for(self, audience_id: str) -> list[Constraint]:
        """Return universal plus audience-specific rules, retaining source evidence."""
        self.audience(audience_id)
        return [
            constraint
            for constraint in self._constraint_map.constraints
            if not constraint.applies_to_audiences or audience_id in constraint.applies_to_audiences
        ]

    def contract_evidence_references(self) -> set[str]:
        """Return canonical contract evidence references for verifier-only resolution."""
        return {reference for contract in self._constraint_map.contracts for reference in contract.evidence}
