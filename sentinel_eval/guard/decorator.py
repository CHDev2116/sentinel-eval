"""``@sentinel_guard`` — async ingress/egress interceptor (two-layer funnel)."""

from __future__ import annotations

import functools
import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from sentinel_eval.config import get_settings
from sentinel_eval.guard.exceptions import SentinelGuardBlocked
from sentinel_eval.guard.funnel import (
    LLM_BLOCK_REASON,
    STATIC_BLOCK_REASON,
    evaluate_egress_funnel,
    evaluate_ingress_funnel,
)
from sentinel_eval.guard.judge import HeuristicSentinelJudge, OllamaSentinelJudge, SentinelJudge
from sentinel_eval.guard.models import SentinelJudgeVerdict
from sentinel_eval.guard.siem import append_threat_incident, build_threat_incident

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])

DEFAULT_FALLBACK = "[Sentinel Block] 偵測到潛在安全風險，請求已被攔截。"


def _extract_user_input(
    fn: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    param_name: str,
) -> str:
    if param_name in kwargs:
        value = kwargs[param_name]
        return "" if value is None else str(value)
    params = list(inspect.signature(fn).parameters.values())
    if args and params:
        value = args[0]
        return "" if value is None else str(value)
    raise TypeError(
        f"sentinel_guard could not resolve {param_name!r}; "
        f"pass it as the first positional argument or keyword.",
    )


def _evaluator_model_name(llm_judge: SentinelJudge, judge_model: str | None) -> str:
    if judge_model:
        return judge_model
    model = getattr(llm_judge, "_model", None)
    if model:
        return str(model)
    return get_settings().ollama_model


def _resolve_llm_judge(
    judge: SentinelJudge | None,
    *,
    use_heuristic_judge: bool,
    judge_model: str | None,
) -> SentinelJudge:
    if judge is not None:
        return judge
    if use_heuristic_judge:
        return HeuristicSentinelJudge()
    return OllamaSentinelJudge(model_name=judge_model)


def _log_siem_block(
    *,
    phase: str,
    user_input: str,
    verdict: SentinelJudgeVerdict,
    target_agent: str,
    evaluator_model: str,
    block_reason: str,
    block_type: str,
    agent_response: str | None = None,
) -> None:
    incident = build_threat_incident(
        phase=phase,
        user_input=user_input,
        verdict=verdict,
        target_agent=target_agent,
        evaluator_model=evaluator_model,
        agent_response=agent_response,
        environment=get_settings().threat_intel_environment,
        block_type=block_type,
        reason=block_reason,
    )
    path = append_threat_incident(incident)
    logger.info("Threat intel logged: %s (%s)", incident.incident_id, path)


def _handle_block(
    *,
    phase: str,
    decision: Any,
    user_input: str,
    target_agent: str,
    evaluator_model: str,
    siem_log: bool,
    raise_on_block: bool,
    fallback_response: str,
    agent_response: str | None = None,
) -> str | None:
    """Return fallback_response if blocked, else None to continue."""
    verdict = decision.verdict
    if verdict is None:
        return None
    reason = decision.reason or "blocked"
    logger.warning(
        "sentinel_guard %s block [%s/%s]: %s",
        phase,
        decision.layer,
        reason,
        verdict.rationale,
    )
    if siem_log:
        _log_siem_block(
            phase=phase,
            user_input=user_input,
            verdict=verdict,
            target_agent=target_agent,
            evaluator_model=evaluator_model,
            block_reason=reason,
            block_type=decision.layer,
            agent_response=agent_response,
        )
    if raise_on_block:
        raise SentinelGuardBlocked(phase, verdict)
    return fallback_response


def sentinel_guard(
    *,
    ingress_check: bool = True,
    egress_check: bool = True,
    fallback_response: str = DEFAULT_FALLBACK,
    judge_model: str | None = None,
    judge: SentinelJudge | None = None,
    input_param: str = "user_input",
    raise_on_block: bool = False,
    use_heuristic_judge: bool = False,
    siem_log: bool = True,
    target_agent: str = "unknown",
) -> Callable[[F], F]:
    """
    Async decorator using the two-layer funnel:

    Heuristic coarse screen (allowlist + static block) → LLM judge fine screen.
    """

    def decorator(fn: F) -> F:
        if not inspect.iscoroutinefunction(fn):
            raise TypeError("sentinel_guard only supports async callables")

        llm_judge = _resolve_llm_judge(
            judge,
            use_heuristic_judge=use_heuristic_judge,
            judge_model=judge_model,
        )
        evaluator_model = _evaluator_model_name(llm_judge, judge_model)

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            user_input = _extract_user_input(fn, args, kwargs, input_param)

            if ingress_check:
                ingress_decision = await evaluate_ingress_funnel(
                    user_input,
                    llm_judge=llm_judge,
                )
                if ingress_decision.blocked:
                    blocked = _handle_block(
                        phase="ingress",
                        decision=ingress_decision,
                        user_input=user_input,
                        target_agent=target_agent,
                        evaluator_model=evaluator_model,
                        siem_log=siem_log,
                        raise_on_block=raise_on_block,
                        fallback_response=fallback_response,
                    )
                    if blocked is not None:
                        return blocked

            agent_output = await fn(*args, **kwargs)

            if egress_check:
                egress_decision = await evaluate_egress_funnel(
                    user_input,
                    "" if agent_output is None else str(agent_output),
                    llm_judge=llm_judge,
                )
                if egress_decision.blocked:
                    blocked = _handle_block(
                        phase="egress",
                        decision=egress_decision,
                        user_input=user_input,
                        target_agent=target_agent,
                        evaluator_model=evaluator_model,
                        siem_log=siem_log,
                        raise_on_block=raise_on_block,
                        fallback_response=fallback_response,
                        agent_response=None if agent_output is None else str(agent_output),
                    )
                    if blocked is not None:
                        return blocked

            return agent_output

        return wrapper  # type: ignore[return-value]

    return decorator


__all__ = [
    "sentinel_guard",
    "STATIC_BLOCK_REASON",
    "LLM_BLOCK_REASON",
]
