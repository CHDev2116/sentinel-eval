import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from sentinel_eval.domain.models import CaseEvaluationResult
from sentinel_eval.domain.report import RunLineage, RunMeta, RunReport
from sentinel_eval.domain.suite_metrics import SuiteMetrics
from sentinel_eval.benchmark.history import append_run_history
from sentinel_eval.config import get_settings
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

    append_run_history(
        metrics=report.metrics,
        model=model_name,
        payload=payload_path,
        report_path=paths[0],
        extra={"full_suite": full_suite},
    )

    if get_settings().write_reliability_chart:
        from sentinel_eval.reporting.reliability_chart import write_reliability_chart

        chart_path = write_reliability_chart(
            report.metrics.calibration,
            os.path.join("reports", "calibration_reliability.svg"),
        )
        if chart_path:
            logger.info("Reliability diagram: %s", chart_path)

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
        "Release pass: %s (%s%%)",
        metrics.release_pass,
        metrics.release_pass_pct,
    )
    if metrics.avg_semantic_cosine is not None:
        logger.info("Avg semantic cosine (primary): %s", metrics.avg_semantic_cosine)
    logger.info("Avg ROUGE-L (advisory): %s", metrics.avg_rouge_l_f1)
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
        if cal.brier_score is not None:
            logger.info(
                "Calibration scoring: Brier=%s ECE=%s (pairs=%s)",
                cal.brier_score,
                cal.ece,
                cal.scored_pairs,
            )
    for tag, m in metrics.by_tag.items():
        logger.info(
            "Tag %s: security=%s%% label=%s%% n=%s",
            tag,
            m.security_pass_pct,
            m.label_match_pct,
            m.cases,
        )
