"""Embedding cosine similarity (optional sentence-transformers)."""

from __future__ import annotations

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def embedding_similarity(
    reference: str,
    candidate: str,
    *,
    model_name: str | None = None,
) -> float | None:
    """
    Cosine similarity in embedding space.

    Returns ``None`` if sentence-transformers is not installed (caller should fallback).
    """
    ref = (reference or "").strip()
    cand = (candidate or "").strip()
    if not ref or not cand:
        return 0.0
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.debug("sentence-transformers not installed; embedding similarity skipped")
        return None

    from sentinel_eval.config import get_settings

    name = model_name or get_settings().embedding_model
    model = SentenceTransformer(name)
    emb = model.encode([ref, cand], normalize_embeddings=True)
    return round(float(_cosine(emb[0].tolist(), emb[1].tolist())), 4)
