# Reports Folder Guide

Runtime outputs are **gitignored** except this README. Generate locally with `python main.py`.

## Layout

| Path | Producer | Format |
|------|----------|--------|
| `evaluation_results.json` | `main.py` | `{ "meta": {...}, "results": [...] }` |
| `latest.json` | `main.py` | Same as above |
| `runs/<timestamp>.json` | `main.py` | Timestamped copy |
| `generated_runs/<timestamp>.json` | `examples/generated_pipeline.py` | Generated batch |
| `async_runs/<timestamp>.jsonl` | `examples/tri_agent.py` | JSONL + meta line |
| `async_latest.jsonl` | `examples/tri_agent.py` | Latest async snapshot |

## Summarize a run

```bash
sentinel-summarize reports/evaluation_results.json
sentinel-summarize reports/evaluation_results.json --markdown
```

## Cleanup

```bash
python -m sentinel_eval.utils.cleanup --keep 2 --dry-run
python -m sentinel_eval.utils.cleanup --keep 2
```

## After heavy evals

Unload models to cool the machine: `ollama stop <model>` or quit the Ollama app.
