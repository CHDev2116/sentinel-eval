import argparse
import json
import logging
import sys

from sentinel_eval.clients.ollama import DEFAULT_MODEL, SentinelTester
from sentinel_eval.config import get_settings
from sentinel_eval.domain.models import CaseEvaluationResult
from sentinel_eval.evaluators.case import evaluate_case
from sentinel_eval.metrics.release_gate import (
    RELEASE_ROUGE_L_THRESHOLD,
    evaluate_advisory_gate,
    evaluate_release_gate,
    log_advisory_gate_report,
    log_release_gate_report,
)
from sentinel_eval.utils.logging_config import setup_logging
from sentinel_eval.utils.payloads import GOLDEN_PAYLOAD, load_payload_cases
from sentinel_eval.utils.reports import log_metrics_summary, write_run_report

logger = logging.getLogger(__name__)
SMOKE_LIMIT = 3


def parse_args():
    parser = argparse.ArgumentParser(
        description="SentinelEval batch runner (defaults to a short smoke run on laptops)."
    )
    parser.add_argument("--all", action="store_true", help="Run the full golden suite.")
    parser.add_argument(
        "--include-generated",
        action="store_true",
        help="Also run payloads/scenarios_generated.json (experimental cases).",
    )
    parser.add_argument(
        "--tags",
        default=None,
        help="Comma-separated tags to filter cases (e.g. injection,benign).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help=f"Run at most N cases (default: {SMOKE_LIMIT} unless --all).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"Ollama model tag (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument("--payload", default=GOLDEN_PAYLOAD, help="Path to test-case JSON.")
    parser.add_argument(
        "--rouge-l-threshold",
        type=float,
        default=0.25,
        help="Minimum ROUGE-L F1 for composite pass.",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Summary lines only (still via logging)."
    )
    parser.add_argument(
        "--release-gate", action="store_true", help="Per-case release gate (ROUGE-L 0.70)."
    )
    parser.add_argument(
        "--advisory-gate", action="store_true", help="Suite-level advisory targets."
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )
    parser.add_argument(
        "--json-logs",
        action="store_true",
        help="Emit structured JSON log lines on stderr.",
    )
    return parser.parse_args()


def resolve_limit(args, total_cases):
    if args.all:
        return total_cases
    if args.limit is not None:
        return min(max(args.limit, 1), total_cases)
    return min(SMOKE_LIMIT, total_cases)


def _log_case_summary(result: CaseEvaluationResult) -> None:
    match_s = "n/a" if result.prediction_match is None else result.prediction_match
    rouge_f1 = result.rouge.rougeL.f1 if result.rouge.rougeL else 0.0
    logger.info(
        "%s: schema=%s label=%s security=%s rougeL=%.2f release=%s composite=%s",
        result.case_id,
        result.schema_validation.is_valid,
        match_s,
        result.security_pass,
        rouge_f1,
        result.release_pass,
        result.composite_pass,
    )


def _log_case_verbose(result: CaseEvaluationResult) -> None:
    logger.info("Running %s — %s", result.case_id, result.description)
    audit = result.audit_output or json.dumps(result.parsed_output.model_dump(), ensure_ascii=False)
    logger.info("Parsed audit: %s", audit)
    logger.info(
        "Schema valid=%s errors=%s",
        result.schema_validation.is_valid,
        result.schema_validation.errors,
    )
    rouge_f1 = result.rouge.rougeL.f1 if result.rouge.rougeL else 0.0
    logger.info("ROUGE-L F1=%.2f", rouge_f1)
    if result.prediction_match is not None:
        logger.info(
            "Label expected=%s predicted=%s match=%s security=%s composite=%s",
            result.expected_is_safe,
            result.parsed_output.is_safe,
            result.prediction_match,
            result.security_pass,
            result.composite_pass,
        )


def main():
    args = parse_args()
    setup_logging(args.log_level or get_settings().log_level, json_logs=args.json_logs)
    model_name = args.model or DEFAULT_MODEL
    tester = SentinelTester(model_name=model_name)
    tag_filter = None
    if args.tags:
        tag_filter = [t.strip() for t in args.tags.split(",") if t.strip()]

    scenarios = load_payload_cases(
        args.payload,
        include_generated=args.include_generated,
        tag_filter=tag_filter,
    )
    total_cases = len(scenarios)
    if total_cases == 0:
        logger.warning("No cases matched filters.")
        return

    run_count = resolve_limit(args, total_cases)
    scenarios = scenarios[:run_count]
    rouge_threshold = RELEASE_ROUGE_L_THRESHOLD if args.release_gate else args.rouge_l_threshold

    limit_note = ""
    if not args.all:
        limit_note = (
            f" (smoke: {run_count}/{total_cases})"
            if args.limit is None
            else f" ({run_count}/{total_cases})"
        )
    logger.info(
        "Batch model=%s prompt=%s cases=%s%s",
        model_name,
        tester.prompt_version,
        run_count,
        limit_note,
    )

    results: list[CaseEvaluationResult] = []
    for case in scenarios:
        if not args.quiet:
            pass  # logged after evaluate
        result = evaluate_case(case, tester, rouge_l_threshold=rouge_threshold)
        results.append(result)
        if args.quiet:
            _log_case_summary(result)
        else:
            _log_case_verbose(result)

    report_path, metrics = write_run_report(
        results,
        model_name=model_name,
        payload_path=args.payload,
        full_suite=args.all,
        extra_meta={
            "include_generated": args.include_generated,
            "tag_filter": tag_filter,
        },
    )
    log_metrics_summary(metrics, model_name)
    logger.info("Run report: %s", report_path)
    logger.info("Completed %s case(s).", run_count)

    exit_code = 0
    if args.release_gate:
        passed, failures = evaluate_release_gate(metrics, results)
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
