"""Deterministic source-grounded scene retrieval for planner and verifier use."""

from __future__ import annotations

from dataclasses import dataclass

from src.models.story import Scene, StoryMap, timecode_to_milliseconds


class SceneNotFoundError(LookupError):
    """Raised when a requested source scene does not exist in the episode package."""


@dataclass(frozen=True, slots=True)
class SceneQuery:
    """Optional filters that combine with AND semantics for predictable retrieval."""

    scene_id: str | None = None
    character_id: str | None = None
    keyword: str | None = None
    emotion: str | None = None
    audience_requirement: str | None = None
    dialogue: str | None = None
    timecode: str | None = None


class SceneSearch:
    """Read-only index over scenes that were already validated during ingestion."""

    def __init__(self, story_map: StoryMap) -> None:
        self._scenes = tuple(story_map.scenes)
        self._by_id = {scene.scene_id: scene for scene in self._scenes}

    def get_by_id(self, scene_id: str) -> Scene:
        """Return an existing scene or fail closed for an unsupported scene reference."""
        try:
            return self._by_id[scene_id]
        except KeyError as error:
            raise SceneNotFoundError(f"Scene does not exist in the episode package: {scene_id}") from error

    def search(self, query: SceneQuery | None = None) -> list[Scene]:
        """Return only source scenes matching every provided filter."""
        query = query or SceneQuery()
        target_millis = timecode_to_milliseconds(query.timecode) if query.timecode else None
        return [scene for scene in self._scenes if self._matches(scene, query, target_millis)]

    @staticmethod
    def _matches(scene: Scene, query: SceneQuery, target_millis: int | None) -> bool:
        searchable_text = " ".join(
            [scene.title, scene.description, *scene.tags, *(line.text for line in scene.dialogue)]
        ).casefold()
        if query.scene_id is not None and scene.scene_id != query.scene_id:
            return False
        if query.character_id is not None and query.character_id not in scene.characters:
            return False
        if query.keyword is not None and query.keyword.casefold() not in searchable_text:
            return False
        if query.emotion is not None and query.emotion.casefold() not in {emotion.casefold() for emotion in scene.emotions}:
            return False
        if query.audience_requirement is not None and query.audience_requirement.casefold() not in {tag.casefold() for tag in scene.tags}:
            return False
        if query.dialogue is not None and not any(query.dialogue.casefold() in line.text.casefold() for line in scene.dialogue):
            return False
        if target_millis is not None:
            start = timecode_to_milliseconds(scene.source_in)
            end = timecode_to_milliseconds(scene.source_out)
            if not start <= target_millis < end:
                return False
        return True
