"""Auditor model access layer (Protocol)."""

from __future__ import annotations

import asyncio
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from sentinel_eval.domain.audit_result import AuditResult


class ModelInferenceParams(BaseModel):
    """Reproducibility knobs passed to the inference backend."""

    temperature: float | None = None
    seed: int | None = None
    top_p: float | None = None
    num_predict: int | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.temperature is not None:
            out["temperature"] = self.temperature
        if self.seed is not None:
            out["seed"] = self.seed
        if self.top_p is not None:
            out["top_p"] = self.top_p
        if self.num_predict is not None:
            out["num_predict"] = self.num_predict
        out.update(self.extra)
        return out

    def for_lineage(self) -> dict[str, Any]:
        return self.to_dict()


@runtime_checkable
class AuditorModel(Protocol):
    """
    Pluggable email-thread auditor (Ollama, OpenAI, vLLM, LM Studio, etc.).

    Implementations must provide sync ``audit``; async ``audit_async`` defaults
    to a thread-pool wrapper when not overridden.
    """

    @property
    def model_name(self) -> str: ...

    @property
    def prompt_version(self) -> str: ...

    @property
    def backend(self) -> str: ...

    @property
    def inference_params(self) -> ModelInferenceParams: ...

    def audit(self, thread: str) -> AuditResult: ...

    async def audit_async(self, thread: str) -> AuditResult: ...


class AuditorAdapter:
    """Mixin-style default async wrapper for sync auditors."""

    async def audit_async(self, thread: str) -> AuditResult:
        return await asyncio.to_thread(self.audit, thread)  # type: ignore[attr-defined]
