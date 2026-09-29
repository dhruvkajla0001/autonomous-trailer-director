"""Story-understanding agent with deterministic, evidence-preserving mock behavior."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from src.models.story import StoryMap, StoryReasoningReview
from src.models.trailer import DecisionLog
from src.providers.base import GenerationRequest, GenerationResponse, LLMProvider, LLMProviderError
from src.repository.episode_repository import load_story_map


class StoryAgent:
    """Creates structured story memory from an authoritative episode package.

    In mock mode this agent performs schema and reference validation only. It does
    not infer missing facts, rewrite source descriptions, or treat source text as
    executable instructions.
    """

    agent_name = "story_agent"
    provider = "deterministic_mock"

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self._provider = provider
        self._decision_logs: list[DecisionLog] = []

    @property
    def decision_logs(self) -> list[DecisionLog]:
        """Return a defensive copy of provider-call observability records."""
        return list(self._decision_logs)

    def build_story_map(self, episode_path: Path) -> StoryMap:
        """Ingest an episode package without fabricating scenes or timecodes."""
        story_map = load_story_map(episode_path)
        if self._provider is None:
            return story_map

        response = self._provider.generate(self._reasoning_request(story_map))
        try:
            review = StoryReasoningReview.model_validate(response.output)
        except ValidationError as error:
            raise LLMProviderError("Story reasoning response failed its strict schema") from error
        self._validate_review_evidence(review, story_map)
        enriched_story_map = story_map.model_copy(update={"premise": review.premise, "uncertainties": review.uncertainties})
        self._record_response(response, review, enriched_story_map)
        return enriched_story_map

    @staticmethod
    def _reasoning_request(story_map: StoryMap) -> GenerationRequest:
        return GenerationRequest(
            request_id=f"story:{story_map.episode_id}",
            purpose="story_understanding",
            system_instruction=(
                "You are a story analyst. Summarize only source-grounded facts. Identify premise, relationships, "
                "events, spoiler candidates, sensitive material, uncertainty, and evidence. Do not invent scenes, "
                "dialogue, people, events, or timestamps. Return JSON with premise, claim_evidence, and uncertainties."
            ),
            untrusted_data={
                "episode_id": story_map.episode_id,
                "characters": [{"id": item.character_id, "name": item.name, "description": item.description} for item in story_map.characters],
                "scenes": [
                    {
                        "scene_id": scene.scene_id,
                        "source_in": scene.source_in,
                        "source_out": scene.source_out,
                        "description": scene.description,
                        "dialogue": [{"id": line.dialogue_id, "text": line.text} for line in scene.dialogue],
                        "untrusted_notes": scene.untrusted_notes,
                    }
                    for scene in story_map.scenes
                ],
                "spoilers": [{"id": spoiler.spoiler_id, "fact": spoiler.protected_fact} for spoiler in story_map.spoilers],
            },
        )

    @staticmethod
    def _validate_review_evidence(review: StoryReasoningReview, story_map: StoryMap) -> None:
        allowed = {
            *story_map.source_refs,
            *(reference for scene in story_map.scenes for reference in scene.source_refs),
            *(f"scene:{scene.scene_id}" for scene in story_map.scenes),
            *(f"dialogue:{line.dialogue_id}" for scene in story_map.scenes for line in scene.dialogue),
        }
        premise_evidence = review.claim_evidence.get("premise", [])
        if not premise_evidence:
            raise LLMProviderError("Story reasoning premise must include source evidence")
        claims = [*review.claim_evidence.values(), *(item.evidence for item in review.uncertainties)]
        unsupported = sorted({reference for evidence in claims for reference in evidence if reference not in allowed})
        if unsupported:
            raise LLMProviderError(f"Story reasoning cited unsupported evidence: {', '.join(unsupported)}")

    def _record_response(self, response: GenerationResponse, review: StoryReasoningReview, story_map: StoryMap) -> None:
        self._decision_logs.append(
            DecisionLog(
                timestamp=datetime.now(timezone.utc),
                agent=self.agent_name,
                decision="LLM story interpretation accepted after evidence grounding.",
                evidence=review.claim_evidence.get("premise", []),
                input_summary="Canonical episode records supplied as untrusted data.",
                output_summary=review.premise,
                validation_status="PASS",
                provider=response.provider,
                tool_calls=["source_evidence_validation"],
                estimated_cost_usd=response.estimated_cost_usd,
                revision=0,
                decision_id=response.request_id,
                input_references=story_map.source_refs,
                output=response.output,
                confidence=1.0 - max((item.confidence for item in review.uncertainties), default=0.0),
                uncertainties=[item.claim for item in review.uncertainties],
            )
        )
