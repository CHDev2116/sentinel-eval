# Benchmark history

Append-only run log for **temporal regression** (prompt drift, model regression, calibration collapse).

| File | Role |
|------|------|
| `index.jsonl` | One JSON object per `sentinel-eval` run (created on first run) |

Each line includes `recorded_at`, `model`, `payload`, and `metrics` (label match, Brier, ECE, ensemble pass, etc.).

```bash
# Inspect trend locally
python -c "from sentinel_eval.benchmark.history import load_history; print(len(load_history()))"
```

CI nightly jobs append when live Ollama runs succeed.
