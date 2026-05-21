"""Prompt registry — metadata for versioned auditor templates."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PromptMetadata(BaseModel):
    """Production prompt registry entry."""

    prompt_id: str
    name: str
    version: str
    author: str = "SentinelEval"
    target_model: str = "local_guard_models"
    optimized_for: list[str] = Field(default_factory=list)
    known_weakness: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    last_calibrated: str = ""
    dataset_version: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


IS_SAFE_V2_2 = PromptMetadata(
    prompt_id="is_safe_v2.2",
    name="Sentinel Email Security Auditor",
    version="2.2",
    author="SentinelEval",
    target_model="local_guard_models",
    optimized_for=[
        "prompt_injection",
        "format_attack",
        "authority_spoof",
        "long_context_override",
    ],
    known_weakness=[
        "multilingual_attacks",
        "quoted_attack_meta_discussion",
        "benign_edge_short_false_positives",
    ],
    failure_modes=[
        "false_positive_benign",
        "false_negative_quoted_injection",
        "rouge_below_release_threshold",
    ],
    last_calibrated="2026-05-21",
    dataset_version="v2.1",
    description=(
        "Structured JSON auditor with mandatory calibration fields "
        "(risk_score, confidence, uncertainty)."
    ),
)

IS_SAFE_V3_0 = PromptMetadata(
    prompt_id="is_safe_v3.0",
    name="Operational Triage Auditor (adversarial)",
    version="3.0",
    author="SentinelEval",
    target_model="local_guard_models",
    optimized_for=[
        "reduced_prompt_overfitting",
        "hidden_rubric_judges",
        "mutation_stress",
    ],
    known_weakness=[
        "weaker_calibration_without_few_shot",
        "higher_variance_across_models",
    ],
    failure_modes=[
        "false_positive_benign",
        "missed_subtle_injection_without_examples",
    ],
    last_calibrated="2026-05-21",
    dataset_version="v2.1",
    description=(
        "SOC-style triage prompt without benchmark framing; scoring via hidden rubric "
        "and optional judge ensemble."
    ),
)

PROMPT_REGISTRY: dict[str, PromptMetadata] = {
    IS_SAFE_V2_2.prompt_id: IS_SAFE_V2_2,
    IS_SAFE_V3_0.prompt_id: IS_SAFE_V3_0,
}

ACTIVE_AUDITOR_PROMPT: PromptMetadata = IS_SAFE_V2_2

# Back-compat alias used across metrics and reports
PROMPT_VERSION = ACTIVE_AUDITOR_PROMPT.prompt_id


def get_active_prompt() -> PromptMetadata:
    from sentinel_eval.config import get_settings

    pid = get_settings().prompt_version
    return PROMPT_REGISTRY.get(pid, ACTIVE_AUDITOR_PROMPT)


def set_active_prompt(prompt_id: str) -> PromptMetadata:
    """Runtime switch (CLI / tests)."""
    global ACTIVE_AUDITOR_PROMPT, PROMPT_VERSION
    meta = PROMPT_REGISTRY[prompt_id]
    ACTIVE_AUDITOR_PROMPT = meta
    PROMPT_VERSION = meta.prompt_id
    return meta
