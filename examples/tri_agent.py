import argparse
import asyncio

from sentinel_eval.clients.ollama import DEFAULT_MODEL
from sentinel_eval.pipelines.tri_agent import run_async_pipeline, write_reports


def parse_args():
    parser = argparse.ArgumentParser(description="Run async tri-agent red-team demo.")
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Max concurrent tasks (default 1 to reduce GPU heat).",
    )
    parser.add_argument("--generator-model", default=DEFAULT_MODEL)
    parser.add_argument("--auditor-model", default=DEFAULT_MODEL)
    parser.add_argument("--judge-model", default=DEFAULT_MODEL)
    parser.add_argument("--startup-stagger-seconds", type=float, default=0.5)
    return parser.parse_args()


def main():
    args = parse_args()
    models = {
        "generator": args.generator_model,
        "auditor": args.auditor_model,
        "judge": args.judge_model,
    }
    results = asyncio.run(
        run_async_pipeline(
            test_count=max(1, args.count),
            max_concurrent_tasks=max(1, args.concurrency),
            generator_model=args.generator_model,
            auditor_model=args.auditor_model,
            judge_model=args.judge_model,
            startup_stagger_seconds=max(0.0, args.startup_stagger_seconds),
        )
    )
    write_reports(results, models)


if __name__ == "__main__":
    main()
