from sentinel_eval.domain.models import SemanticEvalResult
from sentinel_eval.evaluators.rouge_scorer import RougeScorer


class SemanticEvaluator:
    """ROUGE-based semantic alignment (separate from label / security)."""

    def __init__(self, scorer: RougeScorer | None = None):
        self.scorer = scorer or RougeScorer()

    def evaluate(
        self,
        reference: str,
        structured: str,
        raw_candidate: str,
        rouge_l_threshold: float,
    ) -> SemanticEvalResult:
        rouge = self.scorer.score(reference, structured)
        rouge_raw = self.scorer.score(reference, raw_candidate)
        rouge_l_f1 = self.scorer.rouge_l_f1(rouge)
        rouge_l_pass = rouge_l_f1 >= rouge_l_threshold if reference else None
        return SemanticEvalResult(
            rouge=rouge,
            rouge_raw=rouge_raw,
            rouge_l_f1=rouge_l_f1,
            rouge_l_pass=rouge_l_pass,
            rouge_l_threshold=rouge_l_threshold,
        )
