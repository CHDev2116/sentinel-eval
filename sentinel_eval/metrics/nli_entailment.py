"""NLI entailment score (optional cross-encoder or embedding proxy)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def nli_entailment_score(
    reference: str,
    candidate: str,
    *,
    model_name: str | None = None,
) -> float | None:
    """
    P(entailment) that candidate reasoning aligns with reference.

    Uses ``cross-encoder/nli-deberta-v3-small`` when sentence-transformers is installed;
    otherwise falls back to embedding similarity proxy.
    """
    import math

    from sentinel_eval.metrics.embedding_similarity import embedding_similarity
    from sentinel_eval.metrics.semantic_similarity import reasoning_text

    ref = reasoning_text(reference)
    cand = reasoning_text(candidate)
    if not ref.strip() or not cand.strip():
        return 0.0

    try:
        from sentence_transformers import CrossEncoder
    except ImportError:
        return embedding_similarity(ref, cand, model_name=model_name)

    from sentinel_eval.config import get_settings

    cross_name = model_name or get_settings().nli_model
    model = CrossEncoder(cross_name)
    scores = model.predict([(ref, cand)])
    row = scores[0]
    if hasattr(row, "tolist"):
        row = row.tolist()
    if len(row) >= 3:
        exps = [math.exp(float(x)) for x in row]
        total = sum(exps) or 1.0
        return round(exps[1] / total, 4)
    return round(float(row), 4)
