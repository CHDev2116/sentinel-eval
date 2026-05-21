from typing import Any

from sentinel_eval.config import get_settings
from sentinel_eval.domain.models import CaseEvaluationResult, TestCase
from sentinel_eval.evaluators.case_evaluator import CaseEvaluator

_default_evaluator = CaseEvaluator()


def evaluate_case(
    case: TestCase | dict[str, Any],
    tester,
    rouge_l_threshold: float | None = None,
) -> CaseEvaluationResult:
    """Run one case; returns typed CaseEvaluationResult."""
    if rouge_l_threshold is None:
        rouge_l_threshold = get_settings().default_rouge_l_threshold
    return _default_evaluator.evaluate(case, tester, rouge_l_threshold=rouge_l_threshold)


def evaluate_case_dict(
    case: TestCase | dict[str, Any],
    tester,
    rouge_l_threshold: float | None = None,
) -> dict[str, Any]:
    """Legacy helper: same as evaluate_case but returns report dict."""
    return evaluate_case(case, tester, rouge_l_threshold).to_report_dict()
