"""Lightweight semantic similarity (token cosine) — ROUGE supplement, not replacement for labels."""

from __future__ import annotations

import json
import math
import re
from collections import Counter


def reasoning_text(blob: str) -> str:
    """Compare reasoning prose only (ignore JSON keys like is_safe)."""
    text = (blob or "").strip()
    if text.startswith("{"):
        try:
            data = json.loads(text)
            if isinstance(data, dict) and data.get("reasoning"):
                return str(data["reasoning"])
        except json.JSONDecodeError:
            pass
    return text


def _tokenize(text: str) -> Counter[str]:
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    return Counter(tokens)


def token_cosine_similarity(reference: str, candidate: str) -> float:
    """Bag-of-words cosine in [0, 1]. Robust to paraphrase vs exact ROUGE overlap."""
    reference = reasoning_text(reference)
    candidate = reasoning_text(candidate)
    if not reference.strip() or not candidate.strip():
        return 0.0
    ref = _tokenize(reference)
    cand = _tokenize(candidate)
    if not ref or not cand:
        return 0.0
    dot = sum(ref[t] * cand.get(t, 0) for t in ref)
    norm_ref = math.sqrt(sum(v * v for v in ref.values()))
    norm_cand = math.sqrt(sum(v * v for v in cand.values()))
    if norm_ref == 0 or norm_cand == 0:
        return 0.0
    return round(dot / (norm_ref * norm_cand), 4)
