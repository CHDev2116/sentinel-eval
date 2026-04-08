# Reports Folder Guide

This folder stores runtime outputs from different evaluation flows.

## File and Folder Map

- `evaluation_results.json`
  - Backward-compatible batch output from `main.py`.
- `latest.json`
  - Latest batch output snapshot from `main.py`.
- `runs/`
  - Timestamped batch outputs from `main.py` (`YYYYMMDD_HHMMSS.json`).
- `generated_runs/`
  - Timestamped outputs from `core/generated_case_pipeline_demo.py`.
- `async_latest.jsonl`
  - Latest async tri-agent output snapshot.
- `async_runs/`
  - Timestamped async tri-agent outputs (`YYYYMMDD_HHMMSS.jsonl`).

## Suggested Cleanup Policy

- Keep `latest.json` and `async_latest.jsonl` as stable "latest" entry points.
- Keep recent timestamped files for traceability.
- Optionally delete older timestamped files in `generated_runs/`, `async_runs/`, and `runs/` to save space.

## Auto Cleanup Script

Use `core/cleanup_reports.py` to keep only recent timestamped reports.

Preview only:

```bash
python core/cleanup_reports.py --keep 2 --dry-run
```

Apply cleanup:

```bash
python core/cleanup_reports.py --keep 2
```

## Notes

- Do not rename `evaluation_results.json` unless you also update tooling/docs that depend on it.
- Do not move `latest.json` or `async_latest.jsonl` if scripts rely on fixed paths.
