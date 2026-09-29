"""Deterministic mock and replay providers that never require a network or key."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from src.providers.base import GenerationRequest, GenerationResponse, LLMProvider, LLMProviderError


class MockProvider(LLMProvider):
    """Returns committed fixture outputs keyed by stable request ID."""

    provider_name = "mock"

    def __init__(self, fixtures: Mapping[str, dict[str, object]] | None = None) -> None:
        self._fixtures = dict(fixtures or {})

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        try:
            output = self._fixtures[request.request_id]
        except KeyError as error:
            raise LLMProviderError(f"Mock response is not configured for request: {request.request_id}") from error
        stable_output = json.loads(json.dumps(output, sort_keys=True))
        return GenerationResponse(
            request_id=request.request_id,
            provider=self.provider_name,
            model="deterministic-fixture",
            output=stable_output,
            raw_text=json.dumps(stable_output, sort_keys=True),
        )


class ReplayProvider(MockProvider):
    """Replays recorded structured LLM responses from a JSONL artifact."""

    provider_name = "replay"

    @classmethod
    def from_jsonl(cls, path: Path) -> "ReplayProvider":
        """Load one response per line without contacting an LLM provider."""
        if not path.is_file():
            raise LLMProviderError(f"Replay artifact does not exist: {path}")
        fixtures: dict[str, dict[str, object]] = {}
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                request_id = record["request_id"]
                output = record["output"]
            except (json.JSONDecodeError, KeyError, TypeError) as error:
                raise LLMProviderError(f"Invalid replay record at {path}:{line_number}") from error
            if not isinstance(request_id, str) or not isinstance(output, dict):
                raise LLMProviderError(f"Replay record at {path}:{line_number} needs string request_id and object output")
            if request_id in fixtures:
                raise LLMProviderError(f"Duplicate replay request_id at {path}:{line_number}: {request_id}")
            fixtures[request_id] = output
        return cls(fixtures)
