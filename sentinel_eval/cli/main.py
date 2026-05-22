import argparse
import json
import logging

from sentinel_eval.clients.lineage import build_lineage_fields
from sentinel_eval.clients.factory import BACKENDS, create_auditor
from sentinel_eval.clients.ollama import DEFAULT_MODEL
from sentinel_eval.clients.protocol import ModelInferenceParams
from sentinel_eval.config import get_settings
from sentinel_eval.config.settings import get_settings as _get_settings_fn
from sentinel_eval.domain.models import CaseEvaluationResult
from sentinel_eval.evaluators.case import evaluate_case
from sentinel_eval.metrics.release_gate import (
    RELEASE_ROUGE_L_THRESHOLD,
    evaluate_advisory_gate,
    evaluate_release_gate,
    log_advisory_gate_report,
    log_release_gate_report,
)
from sentinel_eval.mutations.engine import parse_mutation_kinds, parse_surface_names
from sentinel_eval.mutations.expand import expand_payload_cases
from sentinel_eval.prompts.registry import get_active_prompt, set_active_prompt
from sentinel_eval.utils.logging_config import setup_logging
from sentinel_eval.utils.payloads import (
    GOLDEN_PAYLOAD,
    load_dataset_manifest,
    load_payload_cases,
    resolve_payload_path,
)
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
        help="Also merge payloads/generated/ (experimental cases).",
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
    parser.add_argument(
        "--payload",
        default=GOLDEN_PAYLOAD,
        help=(
            "Dataset path or alias (v2, golden, generated, mutations, or path to cases JSON)."
        ),
    )
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
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable SQLite LLM response cache (default: cache on).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Model temperature (Ollama options); recorded in run lineage.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Model seed (Ollama options); recorded in run lineage.",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        choices=["is_safe_v2.2", "is_safe_v3.0"],
        help="Auditor prompt: v2.2 (classification+few-shot) or v3.0 (adversarial triage).",
    )
    parser.add_argument(
        "--judge-ensemble",
        action="store_true",
        help="Post-audit weighted judge ensemble (hidden rubric).",
    )
    parser.add_argument(
        "--judge-mode",
        default="heuristic",
        choices=["heuristic", "llm"],
        help="Judge ensemble backend (llm = 3 extra Ollama calls per case).",
    )
    parser.add_argument(
        "--mutate",
        default=None,
        metavar="KINDS",
        help=(
            "Comma-separated mutation kinds or surface aliases applied before audit: "
            "unicode_homoglyph, markdown_nest, quoted_reply, email_footer_injection, "
            "multilingual_rewrite, … or surface names: unicode, markdown, quoted_reply, "
            "email_footer, multilingual."
        ),
    )
    parser.add_argument(
        "--mutate-seed",
        type=int,
        default=None,
        help="RNG seed for mutation application order.",
    )
    parser.add_argument(
        "--expand-surfaces",
        action="store_true",
        help=(
            "Expand each attack case into robust surface variants "
            "(same semantic attack, different packaging)."
        ),
    )
    parser.add_argument(
        "--mutation-surfaces",
        default=None,
        metavar="SURFACES",
        help=(
            "With --expand-surfaces: comma-separated surfaces "
            "(unicode,markdown,quoted_reply,email_footer,multilingual). "
            "Default: all five core robust surfaces."
        ),
    )
    parser.add_argument(
        "--include-plain-surface",
        action="store_true",
        help="With --expand-surfaces: also run unmutated base case as surface=plain.",
    )
    parser.add_argument(
        "--backend",
        default=None,
        choices=list(BACKENDS),
        help="Auditor backend: ollama (default), openai, vllm, lmstudio (OpenAI-compatible HTTP).",
    )
    parser.add_argument(
        "--api-base",
        default=None,
        help="OpenAI-compatible API base URL (e.g. http://localhost:1234/v1 for LM Studio).",
    )
    parser.add_argument(
        "--semantic-backend",
        default=None,
        choices=["token", "embedding", "nli", "hybrid"],
        help="Semantic alignment: token cosine, embedding, NLI, or hybrid (max).",
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


def main() -> int:
    args = parse_args()
    setup_logging(args.log_level or get_settings().log_level, json_logs=args.json_logs)
    settings = get_settings()
    if args.prompt:
        set_active_prompt(args.prompt)
    model_name = args.model or DEFAULT_MODEL
    mutation_kinds = parse_mutation_kinds(args.mutate) if args.mutate else []
    inference = ModelInferenceParams(
        temperature=args.temperature
        if args.temperature is not None
        else settings.model_temperature,
        seed=args.seed if args.seed is not None else settings.model_seed,
    )
    if args.semantic_backend:
        import os

        os.environ["SEMANTIC_BACKEND"] = args.semantic_backend
        _get_settings_fn.cache_clear()
    auditor = create_auditor(
        model_name,
        backend=args.backend,
        use_cache=not args.no_cache,
        inference_params=inference,
        api_base=args.api_base,
    )
    tag_filter = None
    if args.tags:
        tag_filter = [t.strip() for t in args.tags.split(",") if t.strip()]

    scenarios = load_payload_cases(
        args.payload,
        include_generated=args.include_generated,
        tag_filter=tag_filter,
    )
    if args.expand_surfaces:
        scenarios = expand_payload_cases(
            scenarios,
            args.mutation_surfaces,
            include_plain=args.include_plain_surface,
            expand_attacks_only=True,
        )
    total_cases = len(scenarios)
    if total_cases == 0:
        logger.warning("No cases matched filters.")
        return 0

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
    prompt_meta = get_active_prompt()
    dataset_manifest = load_dataset_manifest(resolve_payload_path(args.payload))
    dataset_ver = (
        dataset_manifest.dataset_version if dataset_manifest else prompt_meta.dataset_version
    )
    expand_note = ""
    if args.expand_surfaces:
        expand_note = f" expand_surfaces={args.mutation_surfaces or 'default'}"
    logger.info(
        "Batch model=%s prompt=%s dataset=%s cases=%s judges=%s mutate=%s%s%s",
        model_name,
        auditor.prompt_version,
        dataset_ver,
        run_count,
        args.judge_mode if args.judge_ensemble else "off",
        mutation_kinds or "off",
        expand_note,
        limit_note,
    )

    results: list[CaseEvaluationResult] = []
    for case in scenarios:
        if not args.quiet:
            pass  # logged after evaluate
        result = evaluate_case(
            case,
            auditor,
            rouge_l_threshold=rouge_threshold,
            mutation_kinds=mutation_kinds or None,
            mutation_seed=args.mutate_seed,
            judge_ensemble=args.judge_ensemble,
            judge_ensemble_mode=args.judge_mode,
        )
        results.append(result)
        if args.quiet:
            _log_case_summary(result)
        else:
            _log_case_verbose(result)

    cache = getattr(auditor, "response_cache", None)
    cache_hits = cache.hits if cache else 0
    cache_misses = cache.misses if cache else 0
    lineage = build_lineage_fields(
        payload_path=args.payload,
        include_generated=args.include_generated,
        inference=inference,
        auditor_backend=getattr(auditor, "backend", "unknown"),
        cache_enabled=not args.no_cache and settings.eval_cache_enabled,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
    )
    lineage["judge_ensemble_mode"] = args.judge_mode if args.judge_ensemble else ""
    lineage["mutation_kinds"] = mutation_kinds
    if args.expand_surfaces:
        lineage["mutation_surfaces"] = parse_surface_names(args.mutation_surfaces)
    report_path, metrics = write_run_report(
        results,
        model_name=model_name,
        payload_path=args.payload,
        full_suite=args.all,
        extra_meta={
            "include_generated": args.include_generated,
            "tag_filter": tag_filter,
            "lineage": lineage,
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
    return exit_code


def app() -> int:
    """Console entry point (setuptools: sentinel-eval)."""
    exit_code = main()
    if exit_code:
        raise SystemExit(exit_code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
