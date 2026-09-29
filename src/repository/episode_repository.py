"""Deterministic ingestion and referential-integrity checks for episode data."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from src.models.story import StoryMap


class EpisodeIngestionError(ValueError):
    """Raised when an episode package is malformed or internally inconsistent."""


def load_story_map(path: Path) -> StoryMap:
    """Load one JSON episode package as verified source-of-truth story memory."""
    if not path.is_file():
        raise EpisodeIngestionError(f"Episode package does not exist: {path}")

    try:
        raw_episode = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise EpisodeIngestionError(f"Episode package is not valid JSON: {path}") from error

    try:
        story_map = StoryMap.model_validate(raw_episode)
    except ValidationError as error:
        raise EpisodeIngestionError(f"Episode package failed schema validation: {path}\n{error}") from error

    validate_story_references(story_map)
    return story_map


def validate_story_references(story_map: StoryMap) -> None:
    """Reject references that cannot be grounded in the supplied episode package."""
    character_ids = _unique_ids("character", (character.character_id for character in story_map.characters))
    scene_ids = _unique_ids("scene", (scene.scene_id for scene in story_map.scenes))
    dialogue_ids = _unique_ids(
        "dialogue",
        (line.dialogue_id for scene in story_map.scenes for line in scene.dialogue),
    )
    sensitive_ids = _unique_ids("sensitive content", (item.content_id for item in story_map.sensitive_content))
    spoiler_ids = _unique_ids("spoiler", (item.spoiler_id for item in story_map.spoilers))

    for relationship in story_map.relationships:
        _require_all_exist("relationship character", relationship.character_ids, character_ids, relationship.relationship_id)
    for scene in story_map.scenes:
        _require_all_exist("scene character", scene.characters, character_ids, scene.scene_id)
        _require_all_exist("scene sensitive content", scene.sensitive_content_ids, sensitive_ids, scene.scene_id)
        _require_all_exist("scene protected fact", scene.protected_fact_ids, spoiler_ids, scene.scene_id)
        _require_all_exist(
            "dialogue speaker",
            (line.speaker_character_id for line in scene.dialogue),
            character_ids,
            scene.scene_id,
        )
    for event in [*story_map.major_events, *story_map.emotional_turns]:
        _require_all_exist("event scene", event.scene_ids, scene_ids, event.event_id)
    for sensitive_content in story_map.sensitive_content:
        _require_all_exist("sensitive-content scene", sensitive_content.scene_ids, scene_ids, sensitive_content.content_id)
    for spoiler in story_map.spoilers:
        _require_all_exist("spoiler scene", spoiler.scene_ids, scene_ids, spoiler.spoiler_id)
        _require_all_exist("spoiler dialogue", spoiler.dialogue_ids, dialogue_ids, spoiler.spoiler_id)


def _unique_ids(kind: str, identifiers: object) -> set[str]:
    """Return IDs or raise an ingestion error for a duplicate source identifier."""
    seen: set[str] = set()
    for identifier in identifiers:  # type: ignore[union-attr]
        if identifier in seen:
            raise EpisodeIngestionError(f"Duplicate {kind} ID: {identifier}")
        seen.add(identifier)
    return seen


def _require_all_exist(reference_kind: str, identifiers: object, known_ids: set[str], owner_id: str) -> None:
    """Fail closed when a structured reference lacks source evidence."""
    missing = sorted(set(identifiers) - known_ids)  # type: ignore[arg-type]
    if missing:
        joined = ", ".join(missing)
        raise EpisodeIngestionError(f"{owner_id} has unknown {reference_kind} reference(s): {joined}")
