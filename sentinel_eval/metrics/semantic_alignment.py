"""Unified semantic alignment (token / embedding / NLI / hybrid)."""

from __future__ import annotations

from dataclasses import dataclass

from sentinel_eval.config import get_settings
from sentinel_eval.metrics.embedding_similarity import embedding_similarity
from sentinel_eval.metrics.nli_entailment import nli_entailment_score
from sentinel_eval.metrics.semantic_similarity import reasoning_text, token_cosine_similarity


@dataclass
class SemanticAlignmentScores:
    backend: str
    token_cosine: float = 0.0
    embedding_similarity: float | None = None
    nli_entailment: float | None = None
    primary_score: float = 0.0

    def passes(self, threshold: float) -> bool:
        return self.primary_score >= threshold


def compute_semantic_alignment(reference: str, candidate: str) -> SemanticAlignmentScores:
    settings = get_settings()
    backend = (settings.semantic_backend or "hybrid").lower()
    ref = reasoning_text(reference)
    cand = reasoning_text(candidate)

    token = token_cosine_similarity(ref, cand) if ref and cand else 0.0
    embed = embedding_similarity(ref, cand)
    nli = nli_entailment_score(ref, cand)

    scores = [token]
    if embed is not None:
        scores.append(embed)
    if nli is not None:
        scores.append(nli)

    if backend == "token":
        primary = token
    elif backend == "embedding":
        primary = embed if embed is not None else token
    elif backend == "nli":
        primary = nli if nli is not None else token
    else:  # hybrid — max available (strictest alignment signal)
        primary = max(scores) if scores else 0.0
        backend = "hybrid"

    return SemanticAlignmentScores(
        backend=backend,
        token_cosine=token,
        embedding_similarity=embed,
        nli_entailment=nli,
        primary_score=round(primary, 4),
    )
