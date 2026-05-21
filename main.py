import argparse
import json
import os
import sys

from core.eval_runner import (
    GOLDEN_PAYLOAD,
    RELEASE_ROUGE_L_THRESHOLD,
    evaluate_case,
    evaluate_release_gate,
    load_payload_cases,
    print_metrics_summary,
    print_release_gate_report,
    write_run_report,
)
from core.logic_isolation_test import DEFAULT_MODEL, SentinelTester

SMOKE_LIMIT = 3


def parse_args():
    parser = argparse.ArgumentParser(
        description="SentinelEval batch runner (defaults to a short smoke run on laptops)."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run the full golden suite (heavy on CPU/GPU).",
    )
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
    parser.add_argument(
        "--payload",
        default=GOLDEN_PAYLOAD,
        help="Path to test-case JSON payload.",
    )
    parser.add_argument(
        "--rouge-l-threshold",
        type=float,
        default=0.25,
        help="Minimum ROUGE-L F1 for composite pass (security pass is separate).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only case id + summary lines.",
    )
    parser.add_argument(
        "--release-gate",
        action="store_true",
        help=(
            "After run, enforce suite-level gates (golden scored cases) and "
            f"use ROUGE-L threshold {RELEASE_ROUGE_L_THRESHOLD}."
        ),
    )
    return parser.parse_args()


def resolve_limit(args, total_cases):
    if args.all:
        return total_cases
    if args.limit is not None:
        return min(max(args.limit, 1), total_cases)
    return min(SMOKE_LIMIT, total_cases)


def main():
    args = parse_args()
    model_name = args.model or DEFAULT_MODEL
    tester = SentinelTester(model_name=model_name)
    tag_filter = None
    if args.tags:
        tag_filter = [t.strip() for t in args.tags.split(",") if t.strip()]

    all_scenarios = load_payload_cases(
        args.payload,
        include_generated=args.include_generated,
        tag_filter=tag_filter,
    )
    total_cases = len(all_scenarios)
    if total_cases == 0:
        print("No cases matched filters.")
        return

    run_count = resolve_limit(args, total_cases)
    scenarios = all_scenarios[:run_count]
    rouge_threshold = (
        RELEASE_ROUGE_L_THRESHOLD if args.release_gate else args.rouge_l_threshold
    )

    if args.all:
        limit_note = ""
    elif args.limit is None:
        limit_note = f" (smoke: {run_count}/{total_cases}; use --all for full suite)"
    else:
        limit_note = f" ({run_count}/{total_cases} cases)"

    print(
        f"🛡️  SentinelEval batch — model={model_name}, "
        f"prompt={tester.prompt_version}, cases={run_count}{limit_note}"
    )
    if run_count < total_cases and not args.quiet:
        print(
            "💡 Tip: Full evals are GPU-heavy. Prefer smoke runs; use --all when plugged in."
        )

    results = []
    for case in scenarios:
        if not args.quiet:
            print(f"\n[Running {case['case_id']}] - {case['description']}")

        result = evaluate_case(case, tester, rouge_l_threshold=rouge_threshold)
        results.append(result)

        if not args.quiet:
            print("--- ✅ Parsed Audit ---")
            print(json.dumps(result["parsed_output"], ensure_ascii=False, indent=2))
            print(
                f"--- 🧪 Schema --- valid={result['schema_validation']['is_valid']}, "
                f"errors={result['schema_validation']['errors']}"
            )
            print("--- 📊 ROUGE-L (structured) ---")
            print(f"rougeL F1={result['rouge']['rougeL']['f1']:.2f}")
            if result["prediction_match"] is not None:
                print(
                    f"--- 🎯 Label --- expected_is_safe={result['expected_is_safe']}, "
                    f"predicted={result['parsed_output'].get('is_safe')}, "
                    f"match={result['prediction_match']}, "
                    f"security_pass={result['security_pass']}, "
                    f"composite_pass={result['composite_pass']}"
                )
            print("-" * 30)
        else:
            match_s = "n/a" if result["prediction_match"] is None else result["prediction_match"]
            print(
                f"{result['case_id']}: schema={result['schema_validation']['is_valid']} "
                f"label={match_s} security={result['security_pass']} "
                f"rougeL={result['rouge']['rougeL']['f1']:.2f} "
                f"release={result.get('release_pass')} composite={result['composite_pass']}"
            )

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
    print_metrics_summary(metrics, model_name)
    print(f"\n🧾 Run report: {report_path}")
    print(f"✅ Completed {run_count} case(s).")

    if args.release_gate:
        passed, failures = evaluate_release_gate(metrics, results)
        print_release_gate_report(passed, failures)
        if not passed:
            sys.exit(1)


if __name__ == "__main__":
    main()
