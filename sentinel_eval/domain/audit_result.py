"""Model audit response (backend-agnostic)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AuditResult(BaseModel):
    """Raw + metadata from one auditor model invocation."""

    raw_output: str
    model: str
    prompt_version: str
    backend: str = "unknown"
    cached: bool = False
    latency_ms: float | None = None
    inference_params: dict[str, float | int | str | None] = Field(default_factory=dict)
