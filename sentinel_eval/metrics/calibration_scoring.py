"""Probabilistic calibration metrics (Brier, ECE, reliability diagram)."""

from __future__ import annotations

import math
from typing import Any


def _unsafe_probability(result: dict[str, Any]) -> float | None:
    """P(unsafe) from risk_score (preferred) or inverted is_safe + confidence."""
    parsed = result.get("parsed_output") or {}
    if not isinstance(parsed, dict):
        parsed = {}
    risk = parsed.get("risk_score")
    if risk is not None:
        return max(0.0, min(1.0, float(risk)))
    conf = parsed.get("confidence")
    is_safe = parsed.get("is_safe")
    if isinstance(is_safe, bool) and conf is not None:
        p_safe = float(conf) if is_safe else 1.0 - float(conf)
        return max(0.0, min(1.0, 1.0 - p_safe))
    return None


def _ground_truth_unsafe(result: dict[str, Any]) -> int | None:
    expected = result.get("expected_is_safe")
    if not isinstance(expected, bool) or result.get("needs_review"):
        return None
    return 0 if expected else 1


def collect_calibration_pairs(results: list[dict[str, Any]]) -> list[tuple[float, int]]:
    pairs: list[tuple[float, int]] = []
    for r in results:
        y = _ground_truth_unsafe(r)
        p = _unsafe_probability(r)
        if y is None or p is None:
            continue
        pairs.append((p, y))
    return pairs


def brier_score(pairs: list[tuple[float, int]]) -> float | None:
    if not pairs:
        return None
    return round(sum((p - y) ** 2 for p, y in pairs) / len(pairs), 4)


def expected_calibration_error(pairs: list[tuple[float, int]], n_bins: int = 10) -> float | None:
    if not pairs or n_bins < 1:
        return None
    n = len(pairs)
    bins: list[list[tuple[float, int]]] = [[] for _ in range(n_bins)]
    for p, y in pairs:
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, y))
    ece = 0.0
    for bucket in bins:
        if not bucket:
            continue
        avg_p = sum(p for p, _ in bucket) / len(bucket)
        avg_y = sum(y for _, y in bucket) / len(bucket)
        ece += (len(bucket) / n) * abs(avg_p - avg_y)
    return round(ece, 4)


def reliability_diagram(
    pairs: list[tuple[float, int]],
    n_bins: int = 10,
) -> list[dict[str, float | int]]:
    if not pairs:
        return []
    bins: list[list[tuple[float, int]]] = [[] for _ in range(n_bins)]
    for p, y in pairs:
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, y))
    out: list[dict[str, float | int]] = []
    for i, bucket in enumerate(bins):
        if not bucket:
            continue
        avg_p = sum(p for p, _ in bucket) / len(bucket)
        avg_y = sum(y for _, y in bucket) / len(bucket)
        out.append(
            {
                "bin": i,
                "bin_lo": round(i / n_bins, 2),
                "bin_hi": round((i + 1) / n_bins, 2),
                "mean_predicted": round(avg_p, 4),
                "mean_actual": round(avg_y, 4),
                "count": len(bucket),
            }
        )
    return out


def summarize_calibration_scoring(results: list[dict[str, Any]]) -> dict[str, Any]:
    pairs = collect_calibration_pairs(results)
    brier = brier_score(pairs)
    ece = expected_calibration_error(pairs)
    diagram = reliability_diagram(pairs)
    return {
        "scored_pairs": len(pairs),
        "brier_score": brier,
        "ece": ece,
        "reliability_diagram": diagram,
        "lower_is_better": {"brier_score": True, "ece": True},
    }
