"""Ollama implementation of AuditorModel."""

from __future__ import annotations

import time
from typing import Any

from ollama import Client

from sentinel_eval.clients.protocol import AuditorAdapter, AuditorModel, ModelInferenceParams
from sentinel_eval.clients.lineage import prompt_sha256
from sentinel_eval.clients.response_cache import ResponseCache, audit_cache_key
from sentinel_eval.config import get_settings
from sentinel_eval.domain.audit_result import AuditResult
from sentinel_eval.prompts.builder import PromptBuilder, resolve_prompt_builder
from sentinel_eval.prompts.registry import get_active_prompt
from sentinel_eval.schemas.audit import AUDIT_OUTPUT_SCHEMA


class OllamaAuditor(AuditorAdapter):
    """Local Ollama auditor with optional response cache."""

    backend = "ollama"

    def __init__(
        self,
        model_name: str | None = None,
        *,
        inference_params: ModelInferenceParams | None = None,
        cache: ResponseCache | None = None,
        prompt_version: str | None = None,
        prompt_builder: PromptBuilder | None = None,
    ):
        settings = get_settings()
        self._model_name = model_name or settings.ollama_model
        self._prompt_version = prompt_version or get_active_prompt().prompt_id
        self._prompt_builder = prompt_builder or resolve_prompt_builder(self._prompt_version)
        self._inference = inference_params or ModelInferenceParams(
            temperature=settings.model_temperature,
            seed=settings.model_seed,
        )
        host = settings.ollama_host
        self._client = Client(host=host) if host else Client()
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

    def audit(self, thread: str) -> AuditResult:
        cache_key = audit_cache_key(
            backend=self.backend,
            model=self._model_name,
            prompt_sha256=self._prompt_hash,
            thread=thread,
            inference=self._inference,
            format_schema="audit_v1",
        )
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return AuditResult(
                    raw_output=cached,
                    model=self._model_name,
                    prompt_version=self._prompt_version,
                    backend=self.backend,
                    cached=True,
                    inference_params=self._inference.for_lineage(),
                )

        started = time.perf_counter()
        options = self._inference.to_dict()
        kwargs: dict[str, Any] = {
            "model": self._model_name,
            "messages": [{"role": "user", "content": self._prompt_builder(thread)}],
            "format": AUDIT_OUTPUT_SCHEMA,
        }
        if options:
            kwargs["options"] = options
        response = self._client.chat(**kwargs)
        raw = response["message"]["content"]
        latency_ms = round((time.perf_counter() - started) * 1000, 2)

        if self._cache is not None:
            self._cache.set(cache_key, raw)

        return AuditResult(
            raw_output=raw,
            model=self._model_name,
            prompt_version=self._prompt_version,
            backend=self.backend,
            cached=False,
            latency_ms=latency_ms,
            inference_params=self._inference.for_lineage(),
        )

    @property
    def response_cache(self) -> ResponseCache | None:
        return self._cache


def create_ollama_auditor(
    model_name: str | None = None,
    *,
    use_cache: bool | None = None,
    inference_params: ModelInferenceParams | None = None,
) -> AuditorModel:
    """Factory: Ollama auditor with settings-driven cache."""
    settings = get_settings()
    cache = None
    enabled = settings.eval_cache_enabled if use_cache is None else use_cache
    if enabled:
        cache = ResponseCache(settings.eval_cache_path, enabled=True)
    return OllamaAuditor(
        model_name=model_name,
        inference_params=inference_params,
        cache=cache,
    )
