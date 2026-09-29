"""Typed policy, rights, audience, budget, and change-event models."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import Field

from src.models.story import StrictModel


class Constraint(StrictModel):
    constraint_id: str
    constraint_type: Literal[
        "spoiler", "rating", "actor_rights", "music_rights", "territory",
        "promotional_use", "cultural_respect", "accessibility", "budget",
    ]
    description: str
    applies_to_audiences: list[str] = Field(default_factory=list)
    prohibited_tags: list[str] = Field(default_factory=list)
    required_tags: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(min_length=1)


class Contract(StrictModel):
    contract_id: str
    resource_id: str
    resource_type: Literal["actor", "music", "dialogue", "voice"]
    promotional_use_allowed: bool
    territories: list[str] = Field(min_length=1)
    expires_at: date | None = None
    restrictions: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(min_length=1)


class AudienceProfile(StrictModel):
    audience_id: str
    display_name: str
    objective: str
    preferred_emotions: list[str] = Field(default_factory=list)
    preferred_tags: list[str] = Field(default_factory=list)
    prohibited_tags: list[str] = Field(default_factory=list)
    cultural_guidance: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)


class BudgetConfig(StrictModel):
    max_total_cost_usd: float = Field(gt=0)
    max_model_calls: int = Field(gt=0)
    max_media_analysis_minutes: float = Field(gt=0)
    evidence: list[str] = Field(min_length=1)


class HistoricPerformanceRecord(StrictModel):
    """A retrospective observation that can inform, but never authorize, planning."""

    scene_id: str
    metric: str
    value: float = Field(ge=0)
    note: str


class ConstraintMap(StrictModel):
    contracts: list[Contract]
    constraints: list[Constraint]
    audiences: list[AudienceProfile]
    historic_performance: list[HistoricPerformanceRecord] = Field(default_factory=list)
    budget: BudgetConfig
    source_refs: list[str] = Field(min_length=1)


class ChangeEvent(StrictModel):
    change_id: str
    change_type: Literal["contract", "policy", "audience", "episode", "model"]
    resource_id: str
    previous_value: str
    new_value: str
    reason: str
    evidence: list[str] = Field(min_length=1)
