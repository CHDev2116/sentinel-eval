# Reports Folder Guide

Runtime outputs are **gitignored** except this README. Generate locally with `sentinel-eval`.

<details>
<summary><strong>Layout</strong></summary>

| Path | Producer | Format |
|------|----------|--------|
| `evaluation_results.json` | `sentinel-eval` | `{ "meta": {...}, "results": [...] }` |
| `latest.json` | `sentinel-eval` | Same as above |
| `runs/<timestamp>.json` | `sentinel-eval` | Timestamped copy |
| `generated_runs/<timestamp>.json` | `examples/generated_pipeline.py` | Generated batch |
| `async_runs/<timestamp>.jsonl` | `examples/tri_agent.py` | JSONL + meta line |
| `async_latest.jsonl` | `examples/tri_agent.py` | Latest async snapshot |
| `threat_intel/events.jsonl` | `@sentinel_guard` (siem_log) | Append-only interception stream |
| `threat_latest.jsonl` | `@sentinel_guard` (siem_log) | Mirror of latest threat events |

</details>

<details>
<summary><strong>Summarize a run</strong></summary>

```bash
sentinel-summarize reports/evaluation_results.json
sentinel-summarize reports/evaluation_results.json --markdown

# Security incident dashboard (ASCII briefing from JSONL stream)
sentinel-summarize reports/threat_intel/events.jsonl --incidents

# Markdown table row (CI)
sentinel-summarize reports/threat_intel/events.jsonl --incidents --markdown

# ASCII briefing + logger metrics
sentinel-summarize reports/threat_intel/events.jsonl --incidents --verbose
```

Single-result entries include compact fields for adversarial judging:
`test_case_id`, `attack_vector`, `payload`, `agent_response`,
`security_metrics` (`ingress_breach`, `egress_leak`, `refusal_compliance`, `is_safe`),
and `adversarial_tier` (while keeping legacy keys for compatibility).
Set `meta.target_agent` from CLI via `--target-agent <name>`.

</details>

<details>
<summary><strong>Cleanup</strong></summary>

```bash
python -m sentinel_eval.utils.cleanup --keep 2 --dry-run
python -m sentinel_eval.utils.cleanup --keep 2
```

</details>

<details>
<summary><strong>After heavy evals</strong></summary>

Unload models to cool the machine: `ollama stop <model>` or quit the Ollama app.

</details>
