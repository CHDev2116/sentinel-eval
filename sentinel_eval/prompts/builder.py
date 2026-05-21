"""Resolve versioned prompt builders for auditors and lineage hashing."""

from __future__ import annotations

from collections.abc import Callable

from sentinel_eval.prompts.adversarial import build_operational_triage_prompt
from sentinel_eval.prompts.audit import build_audit_prompt
from sentinel_eval.prompts.registry import PROMPT_VERSION, get_active_prompt

PromptBuilder = Callable[[str], str]

_BUILDERS: dict[str, PromptBuilder] = {
    "is_safe_v2.2": build_audit_prompt,
    "is_safe_v3.0": build_operational_triage_prompt,
}


def resolve_prompt_builder(prompt_id: str | None = None) -> PromptBuilder:
    pid = prompt_id or get_active_prompt().prompt_id
    if pid not in _BUILDERS:
        raise ValueError(f"Unknown prompt_id={pid!r}; known: {sorted(_BUILDERS)}")
    return _BUILDERS[pid]


def build_prompt_for_version(email_thread: str, prompt_id: str | None = None) -> str:
    return resolve_prompt_builder(prompt_id)(email_thread)


def registered_prompt_ids() -> list[str]:
    return sorted(_BUILDERS)


# Default export for backward compatibility
build_audit_prompt_for_active = lambda thread: build_prompt_for_version(thread, PROMPT_VERSION)
