import argparse
import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT_DIR / "reports"


def list_report_files(target_dir, suffix):
    if not target_dir.exists():
        return []
    files = [item for item in target_dir.iterdir() if item.is_file() and item.suffix == suffix]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def cleanup_timestamped_reports(target_dir, suffix, keep, dry_run):
    files = list_report_files(target_dir, suffix)
    to_delete = files[keep:]
    for path in to_delete:
        if dry_run:
            print(f"[DRY RUN] delete: {path}")
        else:
            path.unlink(missing_ok=True)
            print(f"deleted: {path}")
    return len(to_delete), len(files)


def main():
    parser = argparse.ArgumentParser(
        description="Cleanup old report files and keep only recent runs."
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=2,
        help="How many newest files to keep per report category.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview files to delete without deleting them.",
    )
    args = parser.parse_args()

    keep = max(0, args.keep)
    dry_run = args.dry_run

    categories = [
        (REPORTS_DIR / "runs", ".json"),
        (REPORTS_DIR / "generated_runs", ".json"),
        (REPORTS_DIR / "async_runs", ".jsonl"),
    ]

    print(f"🧹 Cleanup started (keep={keep}, dry_run={dry_run})")
    total_deleted = 0
    for folder, suffix in categories:
        deleted_count, total_count = cleanup_timestamped_reports(
            target_dir=folder,
            suffix=suffix,
            keep=keep,
            dry_run=dry_run,
        )
        total_deleted += deleted_count
        print(
            f"- {folder}: total={total_count}, "
            f"{'would_delete' if dry_run else 'deleted'}={deleted_count}"
        )

    print(
        f"✅ Cleanup done. {'Would remove' if dry_run else 'Removed'} "
        f"{total_deleted} file(s)."
    )


if __name__ == "__main__":
    main()
