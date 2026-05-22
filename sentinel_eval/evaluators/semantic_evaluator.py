from sentinel_eval.config import get_settings
from sentinel_eval.domain.models import SemanticEvalResult
from sentinel_eval.evaluators.protocol import CaseEvalContext
from sentinel_eval.evaluators.rouge_scorer import RougeScorer
from sentinel_eval.metrics.semantic_alignment import compute_semantic_alignment


class SemanticEvaluator:
    """Semantic alignment (token / embedding / NLI / hybrid) + ROUGE-L advisory."""

    evaluator_id = "semantic"

    def __init__(self, scorer: RougeScorer | None = None):
        self.scorer = scorer or RougeScorer()

    def evaluate(
        self,
        reference: str,
        structured: str,
        raw_candidate: str,
        rouge_l_threshold: float | None = None,
        semantic_threshold: float | None = None,
    ) -> SemanticEvalResult:
        settings = get_settings()
        rouge_thresh = (
            rouge_l_threshold
            if rouge_l_threshold is not None
            else settings.default_rouge_l_threshold
        )
        sem_thresh = (
            semantic_threshold
            if semantic_threshold is not None
            else settings.default_semantic_threshold
        )

        rouge = self.scorer.score(reference, structured)
        rouge_raw = self.scorer.score(reference, raw_candidate)
        rouge_l_f1 = self.scorer.rouge_l_f1(rouge)

        alignment = compute_semantic_alignment(reference, structured) if reference else None
        primary = alignment.primary_score if alignment else 0.0

        rouge_l_pass = rouge_l_f1 >= rouge_thresh if reference else None
        semantic_pass = primary >= sem_thresh if reference else None

        return SemanticEvalResult(
            rouge=rouge,
            rouge_raw=rouge_raw,
            rouge_l_f1=rouge_l_f1,
            rouge_l_pass=rouge_l_pass,
            rouge_l_threshold=rouge_thresh,
            semantic_cosine=alignment.token_cosine if alignment else 0.0,
            semantic_pass=semantic_pass,
            semantic_threshold=sem_thresh,
            embedding_similarity=alignment.embedding_similarity if alignment else None,
            nli_entailment=alignment.nli_entailment if alignment else None,
            semantic_score=primary,
            semantic_backend=alignment.backend if alignment else "token",
        )

    def evaluate_context(self, ctx: CaseEvalContext) -> SemanticEvalResult:
        return self.evaluate(
            ctx.reference,
            ctx.structured,
            ctx.raw_output,
            rouge_l_threshold=ctx.rouge_l_threshold,
            semantic_threshold=ctx.semantic_threshold,
        )
