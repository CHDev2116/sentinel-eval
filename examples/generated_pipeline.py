import argparse

from sentinel_eval.pipelines.generated import GENERATED_PAYLOAD, run_generated_batch


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate red-team email cases (appends to payloads/generated/)."
    )
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--generator-model", default=None)
    parser.add_argument("--target-model", default=None)
    parser.add_argument("--payload-path", default=GENERATED_PAYLOAD)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_generated_batch(
        count=max(1, args.count),
        generator_model=args.generator_model,
        target_model=args.target_model,
        payload_path=args.payload_path,
    )
