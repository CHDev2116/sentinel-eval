from collections import defaultdict
from typing import Any

from sentinel_eval.domain.report import results_as_dicts
from sentinel_eval.domain.suite_metrics import (
    ClassificationMetrics,
    SuiteMetrics,
    TagMetrics,
)
from sentinel_eval.metrics.calibration import aggregate_calibration_metrics
from sentinel_eval.metrics.classification import compute_classification_metrics
from sentinel_eval.metrics.release_gate import RELEASE_ROUGE_L_THRESHOLD
from sentinel_eval.domain.taxonomy import ALL_TAXONOMY_TAGS
from sentinel_eval.prompts.audit import PROMPT_VERSION


def _pct(num, den):
    if not den:
        return None
    return round(100 * num / den, 1)


def _ensemble_pass_value(result: dict[str, Any]) -> bool | None:
    block = result.get("ensemble_eval")
    if block is None:
        return None
    if isinstance(block, dict):
        return block.get("ensemble_pass")
    return getattr(block, "ensemble_pass", None)


def serialize_rouge(rouge_scores):
    return {
        metric: {
            "precision": round(values.precision, 4),
            "recall": round(values.recall, 4),
            "f1": round(values.fmeasure, 4),
        }
        for metric, values in rouge_scores.items()
    }


def _subset_to_tag_metrics(subset: dict[str, Any]) -> TagMetrics:
    clf = subset.get("classification")
    payload = {k: v for k, v in subset.items() if k != "classification"}
    if isinstance(clf, dict):
        payload["classification"] = ClassificationMetrics.model_validate(clf)
    return TagMetrics.model_validate(payload)


def _metrics_for_subset(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Internal subset builder (dict) before wrapping as TagMetrics."""
    n = len(results)
    if n == 0:
        return {}

    schema_ok = sum(1 for r in results if r["schema_validation"]["is_valid"])
    scored = [r for r in results if r.get("prediction_match") is not None]
    security_scored = [r for r in results if r.get("security_pass") is not None]
    composite_scored = [r for r in results if r.get("composite_pass") is not None]
    release_scored = [r for r in results if r.get("release_pass") is not None]
    ensemble_scored = [r for r in results if _ensemble_pass_value(r) is not None]
    label_ok = sum(1 for r in scored if r["prediction_match"])
    security_ok = sum(1 for r in security_scored if r["security_pass"])
    composite_ok = sum(1 for r in composite_scored if r["composite_pass"])
    release_ok = sum(1 for r in release_scored if r["release_pass"])
    ensemble_ok = sum(1 for r in ensemble_scored if _ensemble_pass_value(r))
    rouge_l = [r["rouge"]["rougeL"]["f1"] for r in results if "rougeL" in r.get("rouge", {})]
    sem_cos = []
    for r in results:
        sem = r.get("semantic_eval") or {}
        if isinstance(sem, dict) and sem.get("semantic_cosine") is not None:
            sem_cos.append(float(sem["semantic_cosine"]))

    n_security = len(security_scored) or n
    n_composite = len(composite_scored) or n
    n_release = len(release_scored) or n
    n_ensemble = len(ensemble_scored)
    classification = compute_classification_metrics(results)

    return {
        "cases": n,
        "schema_valid_pct": _pct(schema_ok, n),
        "label_match_pct": _pct(label_ok, len(scored)) if scored else None,
        "security_pass_pct": _pct(security_ok, n_security),
        "composite_pass_pct": _pct(composite_ok, n_composite),
        "ensemble_pass_pct": _pct(ensemble_ok, n_ensemble) if n_ensemble else None,
        "release_pass_pct": _pct(release_ok, n_release),
        "avg_rouge_l_f1": round(sum(rouge_l) / len(rouge_l), 2) if rouge_l else 0.0,
        "avg_semantic_cosine": round(sum(sem_cos) / len(sem_cos), 2) if sem_cos else None,
        "injection_recall_pct": classification.injection_recall_pct or classification.recall_pct,
        "benign_specificity_pct": classification.benign_specificity_pct
        or classification.specificity_pct,
        "precision_pct": classification.precision_pct,
        "f1_pct": classification.f1_pct,
        "false_positive_rate_pct": classification.false_positive_rate_pct,
        "classification": classification,
    }


def aggregate_metrics(results: list[Any]) -> SuiteMetrics:
    """Compute leaderboard-style metrics from per-case results."""
    dict_results = results_as_dicts(results)
    n = len(dict_results)
    if n == 0:
        return SuiteMetrics()

    overall = _metrics_for_subset(dict_results)
    schema_ok = sum(1 for r in dict_results if r["schema_validation"]["is_valid"])
    scored = [r for r in dict_results if r.get("prediction_match") is not None]
    security_scored = [r for r in dict_results if r.get("security_pass") is not None]
    composite_scored = [r for r in dict_results if r.get("composite_pass") is not None]
    release_scored = [r for r in dict_results if r.get("release_pass") is not None]
    ensemble_scored = [r for r in dict_results if _ensemble_pass_value(r) is not None]
    label_ok = sum(1 for r in scored if r["prediction_match"])
    security_ok = sum(1 for r in security_scored if r["security_pass"])
    composite_ok = sum(1 for r in composite_scored if r["composite_pass"])
    release_ok = sum(1 for r in release_scored if r["release_pass"])
    ensemble_ok = sum(1 for r in ensemble_scored if _ensemble_pass_value(r))
    n_security = len(security_scored) or n
    n_composite = len(composite_scored) or n
    n_release = len(release_scored) or n
    n_ensemble = len(ensemble_scored)

    classification = overall.get("classification")
    if not isinstance(classification, ClassificationMetrics):
        classification = ClassificationMetrics.model_validate(classification or {})

    by_tag: dict[str, TagMetrics] = {}
    tag_buckets: defaultdict[str, list] = defaultdict(list)
    for r in dict_results:
        for tag in r.get("tags") or ["untagged"]:
            tag_buckets[tag].append(r)
    for tag, bucket in sorted(tag_buckets.items()):
        by_tag[tag] = _subset_to_tag_metrics(_metrics_for_subset(bucket))

    taxonomy_buckets: defaultdict[str, list] = defaultdict(list)
    for r in dict_results:
        for tag in r.get("tags") or []:
            if tag in ALL_TAXONOMY_TAGS:
                taxonomy_buckets[tag].append(r)
    by_taxonomy: dict[str, TagMetrics] = {}
    for tag, bucket in sorted(taxonomy_buckets.items()):
        by_taxonomy[tag] = _subset_to_tag_metrics(_metrics_for_subset(bucket))

    surface_buckets: defaultdict[str, list] = defaultdict(list)
    for r in dict_results:
        surface = ""
        meta = r.get("mutation_meta") or {}
        if isinstance(meta, dict):
            surface = meta.get("surface_form") or ""
        for tag in r.get("tags") or []:
            if tag.startswith("surface:"):
                surface = tag.split(":", 1)[1]
                break
        if surface:
            surface_buckets[surface].append(r)
    by_surface: dict[str, TagMetrics] = {}
    for surface, bucket in sorted(surface_buckets.items()):
        by_surface[surface] = _subset_to_tag_metrics(_metrics_for_subset(bucket))

    robust_surface_pass_pct = None
    attack_surface_pcts: list[float] = []
    for surface, tm in by_surface.items():
        if surface == "plain":
            continue
        if tm.security_pass_pct is not None:
            attack_surface_pcts.append(tm.security_pass_pct)
    if attack_surface_pcts:
        robust_surface_pass_pct = min(attack_surface_pcts)

    return SuiteMetrics(
        cases_run=n,
        prompt_version=PROMPT_VERSION,
        schema_valid_pct=overall["schema_valid_pct"],
        schema_valid=f"{schema_ok}/{n}",
        label_match_pct=overall["label_match_pct"],
        label_match=f"{label_ok}/{len(scored)}" if scored else "n/a",
        security_pass_pct=overall["security_pass_pct"],
        security_pass=f"{security_ok}/{n_security}",
        composite_pass_pct=overall["composite_pass_pct"],
        composite_pass=f"{composite_ok}/{n_composite}",
        ensemble_pass_pct=overall["ensemble_pass_pct"],
        ensemble_pass=f"{ensemble_ok}/{n_ensemble}" if n_ensemble else "n/a",
        release_pass_pct=overall["release_pass_pct"],
        release_pass=f"{release_ok}/{n_release}",
        release_rouge_l_threshold=RELEASE_ROUGE_L_THRESHOLD,
        avg_rouge_l_f1=overall["avg_rouge_l_f1"],
        avg_semantic_cosine=overall.get("avg_semantic_cosine"),
        injection_recall_pct=overall["injection_recall_pct"],
        injection_recall=(
            f"{classification.tn}/{classification.tn + classification.fp}"
            if (classification.tn + classification.fp) > 0
            else "n/a"
        ),
        benign_specificity_pct=overall["benign_specificity_pct"],
        benign_specificity=(
            f"{classification.tp}/{classification.tp + classification.fn}"
            if (classification.tp + classification.fn) > 0
            else "n/a"
        ),
        precision_pct=classification.precision_pct,
        precision=(
            f"{classification.tn}/{classification.tn + classification.fn}"
            if (classification.tn + classification.fn) > 0
            else "n/a"
        ),
        f1_pct=classification.f1_pct,
        f1=classification.f1,
        false_positive_rate_pct=classification.false_positive_rate_pct,
        false_positive_rate=classification.false_positive_rate,
        classification=classification,
        calibration=aggregate_calibration_metrics(dict_results),
        by_tag=by_tag,
        by_taxonomy=by_taxonomy,
        by_surface=by_surface,
        robust_surface_pass_pct=robust_surface_pass_pct,
    )
