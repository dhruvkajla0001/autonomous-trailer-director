"""Typed trailer-plan, validation, risk, and observability models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from src.models.story import StrictModel, Timecode, timecode_to_milliseconds


class RiskFlag(StrictModel):
    risk_id: str
    category: Literal["spoiler", "rights", "policy", "cultural", "accessibility", "budget", "source_accuracy", "story_truth"]
    severity: Literal["warning", "failure"]
    message: str
    evidence: list[str] = Field(min_length=1)


class TrailerSegment(StrictModel):
    segment_id: str
    source_in: Timecode
    source_out: Timecode
    scene_id: str
    video: str
    audio: str
    subtitle: str | None = None
    voice_over: str | None = None
    text_card: str | None = None
    transition_after: str | None = None
    reason: str
    evidence: list[str] = Field(min_length=1)
    risk_flags: list[RiskFlag] = Field(default_factory=list)

    @model_validator(mode="after")
    def has_positive_duration(self) -> "TrailerSegment":
        if timecode_to_milliseconds(self.source_out) <= timecode_to_milliseconds(self.source_in):
            raise ValueError("Trailer segment source_out must be after source_in")
        return self


class ValidationCheck(StrictModel):
    check_id: str
    check_type: str
    status: Literal["PASS", "WARN", "FAIL"]
    message: str
    evidence: list[str] = Field(default_factory=list)
    affected_segments: list[str] = Field(default_factory=list)
    recommended_repair: str | None = None


class ValidationResult(StrictModel):
    status: Literal["PASS", "PASS_WITH_WARNINGS", "FAIL"]
    checks: list[ValidationCheck]
    failures: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    affected_segments: list[str] = Field(default_factory=list)
    recommended_repair: str | None = None
    risk_flags: list[RiskFlag] = Field(default_factory=list)


class TrailerPlan(StrictModel):
    trailer_id: str
    audience_id: str
    audience: str
    duration_seconds: float = Field(gt=0)
    audience_objective: str
    audience_promise: str
    emotional_journey: list[str] = Field(min_length=2)
    planning_hypotheses: list[str] = Field(default_factory=list)
    segments: list[TrailerSegment] = Field(min_length=1)
    validation: ValidationResult | None = None
    warnings: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    estimated_cost_usd: float = Field(ge=0)
    lower_cost_fallback: str
    revision: int = Field(ge=0, default=0)


class TrailerSegmentProposal(StrictModel):
    """Strict LLM proposal that must be grounded before becoming an EDL segment."""

    scene_id: str
    source_in: Timecode
    source_out: Timecode
    dialogue_id: str | None = None
    reason: str
    evidence: list[str] = Field(min_length=1)
    text_card: str | None = None
    transition_after: str | None = "cut"


class TrailerReasoningProposal(StrictModel):
    """Optional LLM creative proposal; deterministic code converts and validates it."""

    audience_promise: str
    emotional_journey: list[str] = Field(min_length=2)
    selection_strategy: str
    segments: list[TrailerSegmentProposal] = Field(min_length=1)
    uncertainties: list[str] = Field(default_factory=list)


class SemanticReview(StrictModel):
    """Independent semantic review output from a provider-backed verifier."""

    status: Literal["PASS", "PASS_WITH_WARNINGS", "FAIL"]
    explanation: str
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    affected_segments: list[str] = Field(default_factory=list)
    recommended_repair: str | None = None


class DecisionLog(StrictModel):
    timestamp: datetime
    agent: str
    decision: str
    evidence: list[str]
    input_summary: str
    output_summary: str
    validation_status: Literal["PASS", "PASS_WITH_WARNINGS", "FAIL", "NOT_RUN"]
    risk: list[RiskFlag] = Field(default_factory=list)
    provider: str
    tool_calls: list[str] = Field(default_factory=list)
    estimated_cost_usd: float = Field(ge=0)
    revision: int = Field(ge=0)
    revision_reason: str | None = None
    decision_id: str = ""
    input_references: list[str] = Field(default_factory=list)
    output: dict[str, object] = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0, le=1)
    uncertainties: list[str] = Field(default_factory=list)
