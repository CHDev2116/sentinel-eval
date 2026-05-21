import argparse
import sys

from sentinel_eval.reporting.leaderboard import (
    DEFAULT_LEADERBOARD_PATH,
    format_ascii_table,
    format_markdown_table,
    load_leaderboard,
    register_report,
    scan_and_register,
    sort_entries,
)


def main():
    parser = argparse.ArgumentParser(
        description="SentinelEval model leaderboard (golden 12-case benchmark)."
    )
    parser.add_argument(
        "--file",
        default=DEFAULT_LEADERBOARD_PATH,
        help="Leaderboard JSON path (default: reports/leaderboard.json)",
    )
    parser.add_argument(
        "--register",
        metavar="REPORT",
        help="Register one run report JSON into the leaderboard",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan reports/runs and reports/*.json, merge full-suite runs",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Print markdown table (paste into README)",
    )
    args = parser.parse_args()

    if args.register:
        entry = register_report(args.register, leaderboard_path=args.file)
        print(f"Registered `{entry['model']}` ({entry['prompt_version']}) → {args.file}")
        board = load_leaderboard(args.file)
    elif args.scan:
        count, board = scan_and_register(leaderboard_path=args.file)
        print(f"Scanned and merged {count} report(s) → {args.file}")
    else:
        board = load_leaderboard(args.file)

    entries = sort_entries(board.get("entries", []))
    if not entries:
        print("No leaderboard entries. Run:")
        print("  python main.py --all --model <tag> --quiet")
        print("  sentinel-leaderboard --register reports/evaluation_results.json")
        sys.exit(1)

    if args.markdown:
        print(format_markdown_table(entries))
    else:
        print(f"SentinelEval Leaderboard ({board.get('suite', 'golden-12')})")
        if board.get("updated_at"):
            print(f"Updated: {board['updated_at']}\n")
        print(format_ascii_table(entries))
        print("\nMarkdown: sentinel-leaderboard --markdown")


if __name__ == "__main__":
    main()
