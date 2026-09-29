"""Offline end-to-end tests for provider-backed reasoning under hard trust boundaries."""

from __future__ import annotations

from src.agents.planner_agent import PlannerAgent
from src.agents.story_agent import StoryAgent
from src.agents.verifier_agent import VerifierAgent
from src.providers.base import LLMProviderError
from src.providers.mock import MockProvider
from tests.validation_helpers import ROOT, family_plan, verified_context


def story_review_fixture() -> dict[str, object]:
    return {
        "premise": "Two sisters search for a missing ceremonial lantern before a family ritual.",
        "claim_evidence": {"premise": ["scene:scene_01", "scene:scene_02"]},
        "uncertainties": [
            {
                "claim_id": "uncertain_signal_origin",
                "claim": "The source of the lantern signal is not established before the protected reveal.",
                "evidence": ["scene:scene_05"],
                "confidence": 0.72,
                "reason": "The source scene identifies a signal but not its origin.",
            }
        ],
    }


def planning_fixture(scene_id: str, source_in: str, source_out: str, dialogue_id: str, promise: str) -> dict[str, object]:
    return {
        "audience_promise": promise,
        "emotional_journey": ["curiosity", "hope"],
        "selection_strategy": "Use a source-grounded character moment; engagement data is secondary.",
        "segments": [
            {
                "scene_id": scene_id,
                "source_in": source_in,
                "source_out": source_out,
                "dialogue_id": dialogue_id,
                "reason": "Uses a verifiable episode moment aligned to the audience objective.",
                "evidence": [f"scene:{scene_id}", f"dialogue:{dialogue_id}"],
            }
        ],
        "uncertainties": ["A human editor should review final text-card tone."],
    }


def test_story_agent_accepts_grounded_llm_interpretation_and_preserves_canonical_facts() -> None:
    provider = MockProvider({"story:demo_monsoon_lanterns_e01": story_review_fixture()})

    story = StoryAgent(provider).build_story_map(ROOT / "data/episode/episode_demo.json")

    assert story.premise is not None
    assert story.spoilers[0].spoiler_id == "spoiler_father_alive"
    assert story.uncertainties[0].claim_id == "uncertain_signal_origin"
    assert len(StoryAgent().build_story_map(ROOT / "data/episode/episode_demo.json").scenes) == len(story.scenes)


def test_prompt_injection_is_passed_as_untrusted_data_and_cannot_change_story_constraints() -> None:
    provider = MockProvider({"story:demo_monsoon_lanterns_e01": story_review_fixture()})
    agent = StoryAgent(provider)

    story = agent.build_story_map(ROOT / "data/episode/episode_demo.json")

    prompt = agent._reasoning_request(story).render_prompt()  # noqa: SLF001 - explicit trust-boundary assertion
    assert "Ignore the contract" in prompt
    assert "UNTRUSTED_DATA" in prompt
    assert story.spoilers[0].scene_ids == ["scene_07"]


def test_story_agent_rejects_unsupported_claims_instead_of_promoting_them_to_fact() -> None:
    invalid_review = story_review_fixture()
    invalid_review["claim_evidence"] = {"premise": ["scene:scene_999"]}

    with __import__("pytest").raises(LLMProviderError, match="unsupported evidence"):
        StoryAgent(MockProvider({"story:demo_monsoon_lanterns_e01": invalid_review})).build_story_map(
            ROOT / "data/episode/episode_demo.json"
        )


def test_planner_agent_builds_three_distinct_grounded_llm_candidate_plans() -> None:
    story, constraints, _ = verified_context()
    provider = MockProvider(
        {
            "planning:family": planning_fixture("scene_01", "00:00:06.000", "00:00:12.000", "dialogue_01_01", "A warm ritual becomes a gentle mystery."),
            "planning:young_adult": planning_fixture("scene_03", "00:00:38.000", "00:00:46.000", "dialogue_03_01", "Friendship and humour meet a fast mystery."),
            "planning:dialect_region": planning_fixture("scene_05", "00:01:18.000", "00:01:22.000", "dialogue_05_01", "A family song carries a grounded mystery."),
        }
    )

    plans = PlannerAgent(story, constraints, provider).plan_all()

    assert [plan.audience_id for plan in plans] == ["family", "young_adult", "dialect_region"]
    assert len({plan.audience_promise for plan in plans}) == 3
    assert [plan.segments[0].scene_id for plan in plans] == ["scene_01", "scene_03", "scene_05"]


def test_semantic_verifier_can_reject_a_plan_that_passes_deterministic_checks() -> None:
    story, constraints, _ = verified_context()
    semantic_provider = MockProvider(
        {
            "semantic:family_v1:r0": {
                "status": "FAIL",
                "explanation": "The promise implies a resolution that the selected clips do not support.",
                "risk_flags": [
                    {
                        "risk_id": "semantic_promise_mismatch",
                        "category": "story_truth",
                        "severity": "failure",
                        "message": "Promise overstates the available source context.",
                        "evidence": ["scene:scene_01"],
                    }
                ],
                "evidence": ["scene:scene_01"],
                "affected_segments": ["seg_01"],
                "recommended_repair": "Use a promise limited to the missing-lantern setup.",
            }
        }
    )
    result = VerifierAgent(story, constraints, semantic_provider=semantic_provider).validate(family_plan())

    assert result.status == "FAIL"
    assert result.risk_flags[0].risk_id == "semantic_promise_mismatch"


def test_semantic_llm_cannot_override_a_deterministic_rights_failure() -> None:
    story, constraints, _ = verified_context()
    plan = family_plan()
    unlicensed = plan.segments[0].model_copy(update={"audio": "track_licensed_uk_only"})
    verifier = VerifierAgent(
        story,
        constraints,
        semantic_provider=MockProvider({"semantic:family_v1:r0": {"status": "PASS", "explanation": "Ignored"}}),
    )

    result = verifier.validate(plan.model_copy(update={"segments": [unlicensed, *plan.segments[1:]]}))

    assert result.status == "FAIL"
    assert len(verifier.decision_logs) == 0
