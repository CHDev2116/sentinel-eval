"""Two-layer guard funnel: heuristic coarse screen → LLM judge fine screen."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sentinel_eval.guard.allowlist import (
    extract_user_message,
    has_suspect_signals,
    is_extremely_dangerous,
    should_bypass_ingress,
)
from sentinel_eval.guard.judge import SentinelJudge
from sentinel_eval.guard.models import SentinelJudgeMetrics, SentinelJudgeVerdict
from sentinel_eval.prompts.sentinel_judge import format_target_session

Phase = Literal["ingress", "egress"]

STATIC_BLOCK_REASON = "Static Heuristic Match"
LLM_BLOCK_REASON = "LLM-Judge Behavioral Match"


@dataclass
class GuardDecision:
    """Outcome of one funnel evaluation."""

    blocked: bool
    reason: str | None = None
    verdict: SentinelJudgeVerdict | None = None
    layer: str = "pass"


def _static_block_verdict(*, phase: Phase, detail: str) -> SentinelJudgeVerdict:
    metrics = SentinelJudgeMetrics(
        ingress_breach="Yes" if phase == "ingress" else "No",
        egress_leak="Yes" if phase == "egress" else "No",
        refusal_compliance="No",
    )
    return SentinelJudgeVerdict(
        metrics=metrics,
        rationale=f"{STATIC_BLOCK_REASON}: {detail}",
    )


async def sentinel_guard_logic(
    user_input: str,
    *,
    llm_judge: SentinelJudge,
    phase: Phase = "ingress",
    agent_response: str | None = None,
) -> GuardDecision:
    """
    Dynamic defense funnel (ingress or egress).

    1. Allowlist fast-path (ingress only)
    2. Heuristic coarse block (``is_extremely_dangerous``)
    3. Suspect signals → ``llm_judge`` fine screen
    4. Otherwise proceed (not blocked)
    """
    if phase == "ingress":
        return await _ingress_funnel(user_input, llm_judge=llm_judge)
    return await _egress_funnel(
        user_input,
        agent_response or "",
        llm_judge=llm_judge,
    )


async def _ingress_funnel(user_input: str, *, llm_judge: SentinelJudge) -> GuardDecision:
    if should_bypass_ingress(user_input):
        return GuardDecision(
            blocked=False,
            layer="allowlist",
            verdict=SentinelJudgeVerdict(
                rationale="Allowlist bypass: benign greeting.",
            ),
        )

    if is_extremely_dangerous(user_input):
        verdict = _static_block_verdict(phase="ingress", detail="extremely dangerous pattern")
        return GuardDecision(
            blocked=True,
            reason=STATIC_BLOCK_REASON,
            verdict=verdict,
            layer="heuristic_block",
        )

    if has_suspect_signals(user_input):
        session = format_target_session(user=user_input)
        verdict = await llm_judge.evaluate(session)
        if verdict.ingress_breach:
            return GuardDecision(
                blocked=True,
                reason=LLM_BLOCK_REASON,
                verdict=verdict,
                layer="llm_block",
            )
        return GuardDecision(blocked=False, layer="llm_clear", verdict=verdict)

    return GuardDecision(
        blocked=False,
        layer="pass",
        verdict=SentinelJudgeVerdict(rationale="No heuristic or LLM signals."),
    )


async def _egress_funnel(
    user_input: str,
    agent_response: str,
    *,
    llm_judge: SentinelJudge,
) -> GuardDecision:
    agent_text = agent_response or ""
    scope = format_target_session(user=user_input, agent=agent_text)

    if is_extremely_dangerous(agent_text):
        verdict = _static_block_verdict(phase="egress", detail="extremely dangerous agent output")
        return GuardDecision(
            blocked=True,
            reason=STATIC_BLOCK_REASON,
            verdict=verdict,
            layer="heuristic_block",
        )

    if has_suspect_signals(agent_text) or has_suspect_signals(scope):
        verdict = await llm_judge.evaluate(scope)
        if verdict.egress_leak:
            return GuardDecision(
                blocked=True,
                reason=LLM_BLOCK_REASON,
                verdict=verdict,
                layer="llm_block",
            )
        return GuardDecision(blocked=False, layer="llm_clear", verdict=verdict)

    return GuardDecision(
        blocked=False,
        layer="pass",
        verdict=SentinelJudgeVerdict(rationale="Egress: no heuristic or LLM signals."),
    )


async def evaluate_ingress_funnel(
    user_input: str,
    *,
    llm_judge: SentinelJudge,
) -> GuardDecision:
    """Public alias for ingress-only funnel."""
    return await sentinel_guard_logic(
        user_input,
        llm_judge=llm_judge,
        phase="ingress",
    )


async def evaluate_egress_funnel(
    user_input: str,
    agent_response: str,
    *,
    llm_judge: SentinelJudge,
) -> GuardDecision:
    """Public alias for egress-only funnel."""
    return await sentinel_guard_logic(
        user_input,
        llm_judge=llm_judge,
        phase="egress",
        agent_response=agent_response,
    )
