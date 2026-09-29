"""Tests for source-grounded deterministic scene retrieval."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.agents.story_agent import StoryAgent
from src.tools.scene_search import SceneNotFoundError, SceneQuery, SceneSearch

ROOT = Path(__file__).resolve().parents[1]


def test_scene_search_supports_grounded_filters() -> None:
    search = SceneSearch(StoryAgent().build_story_map(ROOT / "data/episode/episode_demo.json"))

    assert [scene.scene_id for scene in search.search(SceneQuery(character_id="kabir", emotion="humour"))] == ["scene_03"]
    assert [scene.scene_id for scene in search.search(SceneQuery(dialogue="find it together"))] == ["scene_06"]
    assert [scene.scene_id for scene in search.search(SceneQuery(timecode="00:01:18.000"))] == ["scene_05"]


def test_scene_search_rejects_a_nonexistent_scene() -> None:
    search = SceneSearch(StoryAgent().build_story_map(ROOT / "data/episode/episode_demo.json"))

    with pytest.raises(SceneNotFoundError, match="does not exist"):
        search.get_by_id("scene_404")
