import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from sentinel_eval.domain.models import CaseEvaluationResult
from sentinel_eval.domain.report import RunLineage, RunMeta, RunReport
from sentinel_eval.domain.suite_metrics import SuiteMetrics
from sentinel_eval.metrics.aggregation import aggregate_metrics
from sentinel_eval.metrics.classification import log_classification_report
from sentinel_eval.prompts.audit import PROMPT_VERSION

logger = logging.getLogger(__name__)


def build_run_report(
    results: list[CaseEvaluationResult],
    model_name: str,
    payload_path: str,
    full_suite: bool,
    extra_meta: dict | None = None,
) -> RunReport:
    metrics = aggregate_metrics(results)
    meta_fields = {
        "model": model_name,
        "prompt_version": PROMPT_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload_path,
        "full_suite": full_suite,
        "metrics": metrics,
    }
    if extra_meta:
        lineage_raw = extra_meta.pop("lineage", None)
        if lineage_raw is not None:
            meta_fields["lineage"] = (
                lineage_raw
                if isinstance(lineage_raw, RunLineage)
                else RunLineage.model_validate(lineage_raw)
            )
        meta_fields.update(extra_meta)
    meta = RunMeta.model_validate(meta_fields)
    return RunReport(meta=meta, results=results)


def write_run_report(
    results: list[CaseEvaluationResult],
    model_name: str,
    payload_path: str,
    full_suite: bool,
    extra_meta: dict | None = None,
) -> tuple[str, SuiteMetrics]:
    """Persist RunReport to reports/ and return primary path + typed metrics."""
    report = build_run_report(results, model_name, payload_path, full_suite, extra_meta)
    os.makedirs("reports", exist_ok=True)
    os.makedirs(os.path.join("reports", "runs"), exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = [
        os.path.join("reports", "runs", f"{timestamp}.json"),
        os.path.join("reports", "latest.json"),
        os.path.join("reports", "evaluation_results.json"),
    ]
    for path in paths:
        report.write_json(path)

    return paths[0], report.metrics


def load_run_report(path: str | Path) -> RunReport:
    return RunReport.load(path)


def log_metrics_summary(metrics: SuiteMetrics, model_name: str) -> None:
    logger.info(
        "Summary model=%s prompt=%s",
        model_name,
        metrics.prompt_version,
    )
    logger.info(
        "Schema valid: %s (%s%%)",
        metrics.schema_valid,
        metrics.schema_valid_pct,
    )
    logger.info(
        "Security pass: %s (%s%%)",
        metrics.security_pass,
        metrics.security_pass_pct,
    )
    logger.info(
        "Label match: %s (%s%%)",
        metrics.label_match,
        metrics.label_match_pct,
    )
    logger.info(
        "Composite pass: %s (%s%%)",
        metrics.composite_pass,
        metrics.composite_pass_pct,
    )
    if metrics.ensemble_pass != "n/a":
        logger.info(
            "Ensemble pass: %s (%s%%)",
            metrics.ensemble_pass,
            metrics.ensemble_pass_pct,
        )
    logger.info(
        "Release pass: %s (%s%%, rougeL>=%s)",
        metrics.release_pass,
        metrics.release_pass_pct,
        metrics.release_rouge_l_threshold,
    )
    logger.info("Avg ROUGE-L (struct): %s", metrics.avg_rouge_l_f1)
    logger.info(
        "Injection recall: %s (%s%%)",
        metrics.injection_recall,
        metrics.injection_recall_pct,
    )
    logger.info(
        "Benign specificity: %s (%s%%)",
        metrics.benign_specificity,
        metrics.benign_specificity_pct,
    )
    logger.info(
        "Precision / F1: %s (%s%%) / %s%%",
        metrics.precision,
        metrics.precision_pct,
        metrics.f1_pct,
    )
    logger.info("False positive rate: %s%%", metrics.false_positive_rate_pct)
    log_classification_report(metrics)
    cal = metrics.calibration
    if cal and cal.cases_with_risk_score:
        logger.info(
            "Calibration: risk_score n=%s mean=%s high_risk_on_attacks=%s%%",
            cal.cases_with_risk_score,
            cal.mean_risk_score,
            cal.high_risk_on_attacks_pct,
        )
    for tag, m in metrics.by_tag.items():
        logger.info(
            "Tag %s: security=%s%% label=%s%% n=%s",
            tag,
            m.security_pass_pct,
            m.label_match_pct,
            m.cases,
        )
