# Reports Folder Guide

Runtime outputs are **gitignored** except this README. Generate locally with `python main.py`.

## Layout

| Path | Producer | Format |
|------|----------|--------|
| `evaluation_results.json` | `main.py` | `{ "meta": {...}, "results": [...] }` |
| `latest.json` | `main.py` | Same as above |
| `runs/<timestamp>.json` | `main.py` | Timestamped copy |
| `generated_runs/<timestamp>.json` | `generated_case_pipeline_demo.py` | Generated batch |
| `async_runs/<timestamp>.jsonl` | `async_tri_agent_demo.py` | JSONL + meta line |
| `async_latest.jsonl` | `async_tri_agent_demo.py` | Latest async snapshot |

## Summarize a run

```bash
python scripts/summarize_run.py reports/evaluation_results.json
python scripts/summarize_run.py reports/evaluation_results.json --markdown
```

## Cleanup

```bash
python core/cleanup_reports.py --keep 2 --dry-run
python core/cleanup_reports.py --keep 2
```

## After heavy evals

Unload models to cool the machine: `ollama stop <model>` or quit the Ollama app.
