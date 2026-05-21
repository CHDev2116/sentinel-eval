from sentinel_eval.domain.models import RougeMetric, RougeScores
from sentinel_eval.metrics.rouge import calculate_rouge_scores


class RougeScorer:
    """ROUGE-1/2/L alignment vs reference text."""

    def score(self, reference: str, candidate: str) -> RougeScores:
        raw = calculate_rouge_scores(reference, candidate)
        out = RougeScores()
        for key in ("rouge1", "rouge2", "rougeL"):
            values = raw.get(key)
            if values is None:
                continue
            metric = RougeMetric(
                precision=round(values.precision, 4),
                recall=round(values.recall, 4),
                f1=round(values.fmeasure, 4),
            )
            setattr(out, key, metric)
        return out

    @staticmethod
    def rouge_l_f1(scores: RougeScores) -> float:
        if scores.rougeL is None:
            return 0.0
        return scores.rougeL.f1
