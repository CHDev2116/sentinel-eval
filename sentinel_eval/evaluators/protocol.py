"""Evaluator layer protocol — pluggable per-case evaluators."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from sentinel_eval.domain.models import AuditOutput, TestCase


@dataclass
class CaseEvalContext:
    """Inputs shared across evaluators for one case."""

    case: TestCase
    audit: AuditOutput
    raw_output: str
    structured: str
    reference: str
    rouge_l_threshold: float
    semantic_threshold: float
    schema_valid: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Evaluator(Protocol):
    """One evaluation dimension (semantic, schema, security, …)."""

    evaluator_id: str

    def evaluate(self, ctx: CaseEvalContext) -> Any: ...
