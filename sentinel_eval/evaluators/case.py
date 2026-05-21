from typing import Any

from sentinel_eval.config import get_settings
from sentinel_eval.domain.models import CaseEvaluationResult, TestCase
from sentinel_eval.evaluators.case_evaluator import CaseEvaluator

_default_evaluator = CaseEvaluator()


def evaluate_case(
    case: TestCase | dict[str, Any],
    auditor,
    rouge_l_threshold: float | None = None,
    *,
    tester=None,
    mutation_kinds: list[str] | None = None,
    mutation_seed: int | None = None,
    judge_ensemble: bool | None = None,
    judge_ensemble_mode: str | None = None,
) -> CaseEvaluationResult:
    """Run one case; returns typed CaseEvaluationResult."""
    if tester is not None:
        auditor = tester
    if rouge_l_threshold is None:
        rouge_l_threshold = get_settings().default_rouge_l_threshold
    return _default_evaluator.evaluate(
        case,
        auditor,
        rouge_l_threshold=rouge_l_threshold,
        mutation_kinds=mutation_kinds,
        mutation_seed=mutation_seed,
        judge_ensemble=judge_ensemble,
        judge_ensemble_mode=judge_ensemble_mode,
    )
