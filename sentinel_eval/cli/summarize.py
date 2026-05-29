import argparse
import logging
import os
import sys

from sentinel_eval.config import get_settings
from sentinel_eval.metrics.aggregation import aggregate_metrics
from sentinel_eval.metrics.release_gate import (
    evaluate_advisory_gate,
    evaluate_release_gate,
    log_advisory_gate_report,
    log_release_gate_report,
)
from sentinel_eval.reporting.threat_intel import (
    aggregate_threat_intel,
    format_incident_markdown,
    load_threat_incidents,
    log_threat_intel_dashboard,
)
from sentinel_eval.utils.incident_report import summarize_incidents
from sentinel_eval.utils.logging_config import setup_logging
from sentinel_eval.utils.reports import load_run_report, log_metrics_summary

logger = logging.getLogger(__name__)


def _summarize_threat_intel(path: str, *, markdown: bool, verbose: bool) -> int:
    if markdown:
        incidents = load_threat_incidents(path)
        summary = aggregate_threat_intel(incidents)
        print(format_incident_markdown(summary, path))
        print(
            "# Columns: source | total | ingress (%) | egress (%) | block_rate",
            file=sys.stderr,
        )
        return 0

    summarize_incidents(path)
    if verbose:
        incidents = load_threat_incidents(path)
        summary = aggregate_threat_intel(incidents)
        log_threat_intel_dashboard(summary, source=path)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Summarize SentinelEval benchmark JSON or threat-intel JSONL.",
    )
    parser.add_argument(
        "report",
        nargs="?",
        default=None,
        help="Report path (.json benchmark or .jsonl threat intel).",
    )
    parser.add_argument(
        "--markdown", action="store_true", help="Print markdown table row to stdout."
    )
    parser.add_argument("--tags", action="store_true", help="Log per-tag breakdown.")
    parser.add_argument("--release-gate", action="store_true", help="Per-case release gate.")
    parser.add_argument("--advisory-gate", action="store_true", help="Suite advisory gate.")
    parser.add_argument(
        "--incidents",
        action="store_true",
        help="Summarize threat-intel JSONL (SIEM / incident dashboard).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="With --incidents: also emit structured logger dashboard.",
    )
    parser.add_argument("--log-level", default=None, choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--json-logs", action="store_true", help="JSON log lines on stderr.")
    args = parser.parse_args()

    setup_logging(args.log_level or get_settings().log_level, json_logs=args.json_logs)

    report_path = args.report
    if report_path is None:
        report_path = (
            get_settings().threat_intel_events_path
            if args.incidents
            else os.path.join("reports", "evaluation_results.json")
        )

    is_jsonl = report_path.endswith(".jsonl")
    if args.incidents or is_jsonl:
        return _summarize_threat_intel(
            report_path,
            markdown=args.markdown,
            verbose=args.verbose,
        )

    run_report = load_run_report(report_path)
    metrics = run_report.metrics
    if metrics.cases_run == 0 and run_report.results:
        metrics = aggregate_metrics(run_report.results)
    model = run_report.meta.model
    prompt = metrics.prompt_version or run_report.meta.prompt_version

    if args.markdown:
        release = metrics.release_pass_pct
        release_s = f"{release}%" if release is not None else "—"
        print(
            f"| `{model}` | **{metrics.schema_valid_pct}%** | "
            f"**{metrics.label_match_pct}%** | "
            f"**{metrics.avg_rouge_l_f1}** | "
            f"{release_s} | "
            f"`{prompt}` |"
        )
        print(
            "# Register: sentinel-leaderboard --register",
            report_path,
            file=sys.stderr,
        )
        return

    logger.info("Model: %s", model)
    logger.info("Prompt: %s", prompt)
    logger.info("Report: %s", report_path)
    log_metrics_summary(metrics, model)

    if args.tags and metrics.by_tag:
        for tag, m in metrics.by_tag.items():
            logger.info("Tag %s: %s", tag, m)

    exit_code = 0
    if args.release_gate:
        passed, failures = evaluate_release_gate(metrics, run_report.results)
        log_release_gate_report(passed, failures)
        if not passed:
            exit_code = 1
    if args.advisory_gate:
        passed, failures = evaluate_advisory_gate(metrics)
        log_advisory_gate_report(passed, failures)
        if not passed:
            exit_code = 1
    if exit_code:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
