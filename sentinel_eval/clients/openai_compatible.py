"""OpenAI-compatible HTTP auditor (OpenAI, vLLM, LM Studio, llama.cpp server)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from sentinel_eval.clients.cached_auditor import CachedAuditorMixin
from sentinel_eval.clients.protocol import AuditorAdapter, AuditorModel, ModelInferenceParams
from sentinel_eval.clients.lineage import prompt_sha256
from sentinel_eval.clients.response_cache import ResponseCache
from sentinel_eval.config import get_settings
from sentinel_eval.prompts.builder import PromptBuilder, resolve_prompt_builder
from sentinel_eval.prompts.registry import get_active_prompt


class OpenAICompatibleAuditor(CachedAuditorMixin, AuditorAdapter):
    """
    Chat completions via OpenAI-compatible REST API.

    Works with OpenAI, vLLM (--api), LM Studio, llama.cpp server, etc.
    Set ``openai_api_base`` to the provider root (e.g. http://localhost:1234/v1).
    """

    backend = "openai_compatible"

    def __init__(
        self,
        model_name: str | None = None,
        *,
        api_base: str | None = None,
        api_key: str | None = None,
        inference_params: ModelInferenceParams | None = None,
        cache: ResponseCache | None = None,
        prompt_version: str | None = None,
        prompt_builder: PromptBuilder | None = None,
        timeout_sec: float = 120.0,
    ):
        settings = get_settings()
        self._model_name = model_name or settings.openai_model
        self._api_base = (api_base or settings.openai_api_base).rstrip("/")
        self._api_key = api_key or settings.openai_api_key
        self._timeout_sec = timeout_sec
        self._prompt_version = prompt_version or get_active_prompt().prompt_id
        self._prompt_builder = prompt_builder or resolve_prompt_builder(self._prompt_version)
        self._inference = inference_params or ModelInferenceParams(
            temperature=settings.model_temperature,
            seed=settings.model_seed,
        )
        self._cache = cache
        self._prompt_hash = prompt_sha256(self._prompt_builder)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def prompt_version(self) -> str:
        return self._prompt_version

    @property
    def inference_params(self) -> ModelInferenceParams:
        return self._inference

    def _chat_completion(self, prompt: str) -> str:
        url = f"{self._api_base}/chat/completions"
        body: dict[str, Any] = {
            "model": self._model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self._inference.temperature,
        }
        if self._inference.seed is not None:
            body["seed"] = self._inference.seed
        body.update(self._inference.extra)

        data = json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_sec) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI-compatible API error {exc.code}: {detail}") from exc

        choices = payload.get("choices") or []
        if not choices:
            raise RuntimeError(f"Empty choices from {url}")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content:
            raise RuntimeError("Missing message.content in chat completion response")
        return str(content)

    def audit(self, thread: str):
        return self._audit_with_cache(thread, invoke_model=self._chat_completion)
