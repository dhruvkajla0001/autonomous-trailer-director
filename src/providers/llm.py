"""Optional local Ollama adapter using only the Python standard library."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.providers.base import GenerationRequest, GenerationResponse, LLMProvider, LLMProviderError


class OllamaProvider(LLMProvider):
    """Calls a local Ollama server only when the caller explicitly selects it.

    Configure with TRAILER_DIRECTOR_OLLAMA_URL and TRAILER_DIRECTOR_OLLAMA_MODEL.
    The default expects Ollama's local /api/generate endpoint and llama3.2 model.
    """

    provider_name = "ollama"

    def __init__(self, base_url: str | None = None, model: str | None = None, timeout_seconds: float = 45.0) -> None:
        self._base_url = (base_url or os.environ.get("TRAILER_DIRECTOR_OLLAMA_URL", "http://127.0.0.1:11434")).rstrip("/")
        self._model = model or os.environ.get("TRAILER_DIRECTOR_OLLAMA_MODEL", "llama3.2")
        self._timeout_seconds = timeout_seconds

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Request JSON-only output from a local server; no credentials are used."""
        payload = json.dumps(
            {
                "model": self._model,
                "prompt": request.render_prompt(),
                "format": "json",
                "stream": False,
                "options": {"temperature": 0},
            }
        ).encode("utf-8")
        http_request = Request(
            url=f"{self._base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(http_request, timeout=self._timeout_seconds) as response:  # noqa: S310 - configured local endpoint only
                payload_data = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as error:
            raise LLMProviderError(
                f"Local Ollama provider is unavailable at {self._base_url}. "
                "Use mock/replay mode or start the local service."
            ) from error
        raw_text = payload_data.get("response")
        if not isinstance(raw_text, str):
            raise LLMProviderError("Local Ollama response does not contain a string response field")
        try:
            output = json.loads(raw_text)
        except json.JSONDecodeError as error:
            raise LLMProviderError("Local Ollama did not return the required JSON object") from error
        if not isinstance(output, dict):
            raise LLMProviderError("Local Ollama JSON output must be an object")
        return GenerationResponse(
            request_id=request.request_id,
            provider=self.provider_name,
            model=self._model,
            output=output,
            raw_text=raw_text,
        )
