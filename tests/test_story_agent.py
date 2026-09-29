"""Behavior tests for deterministic story ingestion."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.agents.story_agent import StoryAgent
from src.repository.episode_repository import EpisodeIngestionError

ROOT = Path(__file__).resolve().parents[1]
DEMO_EPISODE = ROOT / "data" / "episode" / "episode_demo.json"


def test_story_agent_preserves_authoritative_scenes_and_spoilers() -> None:
    """The agent returns the supplied story memory without inventing source facts."""
    story_map = StoryAgent().build_story_map(DEMO_EPISODE)

    assert [scene.scene_id for scene in story_map.scenes] == [f"scene_{number:02d}" for number in range(1, 9)]
    assert story_map.spoilers[0].spoiler_id == "spoiler_father_alive"
    assert story_map.scenes[-1].source_out == "00:02:30.000"


def test_story_agent_rejects_unknown_scene_reference(tmp_path: Path) -> None:
    """A story event cannot cite a scene absent from the episode package."""
    episode = json.loads(DEMO_EPISODE.read_text(encoding="utf-8"))
    episode["major_events"][0]["scene_ids"] = ["scene_missing"]
    malformed_path = tmp_path / "episode.json"
    malformed_path.write_text(json.dumps(episode), encoding="utf-8")

    with pytest.raises(EpisodeIngestionError, match="unknown event scene"):
        StoryAgent().build_story_map(malformed_path)
