"""Typed, evidence-backed story memory models."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Timecode = Annotated[
    str,
    StringConstraints(pattern=r"^\d{2}:\d{2}:\d{2}\.\d{3}$"),
]

_TIMECODE_PATTERN = re.compile(r"^(?P<hours>\d{2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})\.(?P<millis>\d{3})$")


def timecode_to_milliseconds(value: str) -> int:
    """Convert a validated HH:MM:SS.mmm source timecode to milliseconds."""
    match = _TIMECODE_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError(f"Invalid timecode: {value!r}; expected HH:MM:SS.mmm")
    parts = {name: int(number) for name, number in match.groupdict().items()}
    if parts["minutes"] > 59 or parts["seconds"] > 59:
        raise ValueError(f"Invalid timecode: {value!r}; minutes and seconds must be below 60")
    return (((parts["hours"] * 60) + parts["minutes"]) * 60 + parts["seconds"]) * 1000 + parts["millis"]


class StrictModel(BaseModel):
    """Reject misspelled fields in source-of-truth data."""

    model_config = ConfigDict(extra="forbid")


class Character(StrictModel):
    character_id: str
    name: str
    description: str
    source_refs: list[str] = Field(min_length=1)


class Relationship(StrictModel):
    relationship_id: str
    character_ids: list[str] = Field(min_length=2, max_length=2)
    description: str
    source_refs: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class DialogueLine(StrictModel):
    dialogue_id: str
    speaker_character_id: str
    text: str
    source_in: Timecode
    source_out: Timecode
    dialect_track: str | None = None
    translation: str | None = None

    @model_validator(mode="after")
    def has_positive_duration(self) -> "DialogueLine":
        if timecode_to_milliseconds(self.source_out) <= timecode_to_milliseconds(self.source_in):
            raise ValueError("Dialogue source_out must be after source_in")
        return self


class Scene(StrictModel):
    scene_id: str
    source_in: Timecode
    source_out: Timecode
    title: str
    description: str
    characters: list[str]
    actors: list[str]
    dialogue: list[DialogueLine] = Field(default_factory=list)
    emotions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    sensitive_content_ids: list[str] = Field(default_factory=list)
    protected_fact_ids: list[str] = Field(default_factory=list)
    audio_assets: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(min_length=1)
    untrusted_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def has_valid_range_and_dialogue(self) -> "Scene":
        start = timecode_to_milliseconds(self.source_in)
        end = timecode_to_milliseconds(self.source_out)
        if end <= start:
            raise ValueError("Scene source_out must be after source_in")
        for line in self.dialogue:
            if not (start <= timecode_to_milliseconds(line.source_in) < timecode_to_milliseconds(line.source_out) <= end):
                raise ValueError(f"Dialogue {line.dialogue_id} lies outside scene {self.scene_id}")
        return self


class StoryEvent(StrictModel):
    event_id: str
    description: str
    scene_ids: list[str] = Field(min_length=1)
    source_refs: list[str] = Field(min_length=1)
    emotional_turn: str | None = None


class Spoiler(StrictModel):
    spoiler_id: str
    protected_fact: str
    severity: str = Field(pattern=r"^(major|resolution)$")
    scene_ids: list[str] = Field(min_length=1)
    dialogue_ids: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(min_length=1)


class SensitiveContent(StrictModel):
    content_id: str
    category: str
    description: str
    scene_ids: list[str] = Field(min_length=1)
    source_refs: list[str] = Field(min_length=1)


class UncertainClaim(StrictModel):
    """A model observation retained as uncertain instead of being promoted to fact."""

    claim_id: str
    claim: str
    evidence: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    reason: str


class StoryReasoningReview(StrictModel):
    """Strict schema for optional LLM story interpretation over canonical source data."""

    premise: str
    claim_evidence: dict[str, list[str]] = Field(default_factory=dict)
    uncertainties: list[UncertainClaim] = Field(default_factory=list)


class StoryMap(StrictModel):
    episode_id: str
    title: str
    is_demo_data: bool
    duration_seconds: int = Field(gt=0)
    characters: list[Character]
    relationships: list[Relationship]
    scenes: list[Scene]
    major_events: list[StoryEvent]
    emotional_turns: list[StoryEvent]
    spoilers: list[Spoiler]
    sensitive_content: list[SensitiveContent]
    source_refs: list[str] = Field(min_length=1)
    premise: str | None = None
    uncertainties: list[UncertainClaim] = Field(default_factory=list)
