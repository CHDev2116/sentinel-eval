"""Shared cache + audit flow for AuditorModel implementations."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from sentinel_eval.clients.protocol import ModelInferenceParams
from sentinel_eval.clients.response_cache import ResponseCache, audit_cache_key
from sentinel_eval.domain.audit_result import AuditResult
from sentinel_eval.prompts.builder import PromptBuilder


class CachedAuditorMixin:
    """Mixin: prompt build, optional SQLite cache, AuditResult envelope."""

    backend: str
    _model_name: str
    _prompt_version: str
    _prompt_builder: PromptBuilder
    _inference: ModelInferenceParams
    _cache: ResponseCache | None
    _prompt_hash: str

    @property
    def response_cache(self) -> ResponseCache | None:
        return self._cache

    def _audit_with_cache(
        self,
        thread: str,
        *,
        invoke_model: Callable[[str], str],
        format_schema: str = "audit_v1",
    ) -> AuditResult:
        cache_key = audit_cache_key(
            backend=self.backend,
            model=self._model_name,
            prompt_sha256=self._prompt_hash,
            thread=thread,
            inference=self._inference,
            format_schema=format_schema,
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
        prompt = self._prompt_builder(thread)
        raw = invoke_model(prompt)
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
