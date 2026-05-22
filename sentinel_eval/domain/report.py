"""Run report envelope (meta + per-case results)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from sentinel_eval.domain.models import (
    AuditOutput,
    CaseEvaluationResult,
    RougeMetric,
    RougeScores,
    SchemaValidationResult,
)
from sentinel_eval.domain.suite_metrics import SuiteMetrics
from sentinel_eval.prompts.audit import PROMPT_VERSION


def _rouge_metric_from_dict(raw: dict[str, Any] | None) -> RougeMetric | None:
    if not raw:
        return None
    return RougeMetric(
        precision=float(raw.get("precision", 0.0)),
        recall=float(raw.get("recall", 0.0)),
        f1=float(raw.get("f1", 0.0)),
    )


def _rouge_scores_from_dict(data: dict[str, Any] | None) -> RougeScores:
    if not data:
        return RougeScores()
    scores = RougeScores()
    for key in ("rouge1", "rouge2", "rougeL"):
        metric = _rouge_metric_from_dict(data.get(key))
        if metric is not None:
            setattr(scores, key, metric)
    return scores


def case_result_from_dict(data: dict[str, Any]) -> CaseEvaluationResult:
    """Load one report result item (legacy JSON on disk)."""
    payload = dict(data)
    if isinstance(payload.get("parsed_output"), dict):
        payload["parsed_output"] = AuditOutput.model_validate(payload["parsed_output"])
    if isinstance(payload.get("schema_validation"), dict):
        payload["schema_validation"] = SchemaValidationResult.model_validate(
            payload["schema_validation"]
        )
    payload["rouge"] = _rouge_scores_from_dict(payload.get("rouge"))
    payload["rouge_raw"] = _rouge_scores_from_dict(payload.get("rouge_raw"))
    return CaseEvaluationResult.model_validate(payload)


def results_as_dicts(
    results: list[CaseEvaluationResult] | list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in results:
        if isinstance(item, CaseEvaluationResult):
            out.append(item.to_report_dict())
        else:
            out.append(item)
    return out


class RunLineage(BaseModel):
    """Reproducibility fingerprints for production eval infra."""

    prompt_sha256: str = ""
    dataset_sha256: str = ""
    dataset_version: str = ""
    auditor_backend: str = ""
    model_temperature: float | None = None
    model_seed: int | None = None
    model_params: dict[str, Any] = Field(default_factory=dict)
    cache_enabled: bool = False
    cache_hits: int = 0
    cache_misses: int = 0
    rubric_version: str = ""
    judge_ensemble_mode: str = ""
    mutation_kinds: list[str] = Field(default_factory=list)
    mutation_surfaces: list[str] = Field(default_factory=list)


class RunMeta(BaseModel):
    model: str
    prompt_version: str = PROMPT_VERSION
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    payload: str = ""
    full_suite: bool = False
    metrics: SuiteMetrics = Field(default_factory=SuiteMetrics)
    lineage: RunLineage = Field(default_factory=RunLineage)

    @field_validator("metrics", mode="before")
    @classmethod
    def coerce_metrics(cls, value: Any) -> SuiteMetrics:
        if isinstance(value, SuiteMetrics):
            return value
        if isinstance(value, dict):
            return SuiteMetrics.model_validate(value)
        return SuiteMetrics()

    @field_validator("lineage", mode="before")
    @classmethod
    def coerce_lineage(cls, value: Any) -> RunLineage:
        if isinstance(value, RunLineage):
            return value
        if isinstance(value, dict):
            return RunLineage.model_validate(value)
        return RunLineage()

    include_generated: bool | None = None
    tag_filter: list[str] | None = None

    @model_validator(mode="before")
    @classmethod
    def _split_flat_lineage(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        payload = dict(data)
        lineage_raw = payload.pop("lineage", None)
        if isinstance(lineage_raw, RunLineage):
            payload["lineage"] = lineage_raw.model_dump()
            return payload
        if lineage_raw is None:
            lineage_raw = {}
        elif hasattr(lineage_raw, "model_dump"):
            lineage_raw = lineage_raw.model_dump()
        elif not isinstance(lineage_raw, dict):
            lineage_raw = {}
        for key in RunLineage.model_fields:
            if key in payload:
                lineage_raw[key] = payload.pop(key)
        if lineage_raw:
            payload["lineage"] = lineage_raw
        return payload


class RunReport(BaseModel):
    meta: RunMeta
    results: list[CaseEvaluationResult] = Field(default_factory=list)

    def results_as_dicts(self) -> list[dict[str, Any]]:
        return [r.to_report_dict() for r in self.results]

    def to_json_dict(self) -> dict[str, Any]:
        meta_body = self.meta.model_dump(exclude={"metrics", "lineage"})
        lineage_body = self.meta.lineage.model_dump()
        return {
            "meta": {
                **meta_body,
                **lineage_body,
                "metrics": self.meta.metrics.to_dict(),
            },
            "results": self.results_as_dicts(),
        }

    @property
    def metrics(self) -> SuiteMetrics:
        return self.meta.metrics

    def write_json(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fp:
            json.dump(self.to_json_dict(), fp, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> RunReport:
        with Path(path).open(encoding="utf-8") as fp:
            data = json.load(fp)
        if isinstance(data, list):
            return cls(
                meta=RunMeta(model="unknown", payload=""),
                results=[case_result_from_dict(item) for item in data],
            )
        if not isinstance(data, dict) or "results" not in data:
            raise ValueError(f"Unrecognized report format: {path}")
        meta_raw = data.get("meta") or {}
        results = [case_result_from_dict(item) for item in data["results"]]
        return cls(meta=RunMeta.model_validate(meta_raw), results=results)
