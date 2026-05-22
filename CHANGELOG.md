# Changelog

## v0.12.0

- **Multi-backend auditors**: `create_auditor()` with `ollama`, `openai`, `vllm`, `lmstudio` (OpenAI-compatible HTTP).
- **Semantic backends**: `token`, `embedding`, `nli`, `hybrid` via optional `[semantic]` extra (sentence-transformers).
- **Reliability diagram**: auto-write `reports/calibration_reliability.svg` after each run.
- **Evaluator Protocol**: `CaseEvalContext` + `Evaluator` protocol; all core evaluators implement `evaluate_context()`.

## v0.11.0

- **Calibration scoring**: Brier score, ECE, reliability diagram in `meta.metrics.calibration`.
- **Attack taxonomy**: fine-grained golden tags (`instruction_override`, `format_attack`, …); dataset **v2.2**.
- **Semantic primary**: token-cosine alignment for composite/release; ROUGE-L advisory.
- **Temporal tracking**: `benchmarks/history/index.jsonl` appended each run.
- **CI**: label snapshot gate, benchmark artifacts, nightly model matrix (llama3.1 / gemma / mistral).

## v0.10.0

- **Adversarial eval**: `is_safe_v3.0` operational triage prompt; hidden rubric (`prompts/rubric.py`).
- **Judge ensemble**: security / reasoning / calibration judges with weighted voting (`--judge-ensemble`).
- **Mutation engine** + **`payloads/mutations/`** suite (`mut-1.0`, per-case `mutation_kinds`).
- **Robust surface expansion** (`--expand-surfaces`, `--payload robust`): TC-001 → unicode / markdown / quoted_reply / email_footer / multilingual variants; `by_surface` + `robust_surface_pass_pct` in reports.
- **Metrics**: `ensemble_pass_pct` in `SuiteMetrics` and reports.

## v0.9.0

- **AuditorModel** protocol and `OllamaAuditor`; `SentinelTester` legacy facade.
- **Run lineage**: `prompt_sha256`, `dataset_sha256`, temperature/seed in report `meta`.
- **SQLite response cache** for LLM outputs (`--no-cache` to disable).

## v0.8.0

- **CLI**: `sentinel-eval` / `python -m sentinel_eval` replace root `main.py`.
- **Payloads**: versioned layout `payloads/v2/`, `payloads/generated/` with `dataset_version` envelopes + manifests.
- **Prompt registry**: `PromptMetadata` for `is_safe_v2.2` (optimized_for, known_weakness, calibration date).

## v0.7.0

- **Prompt `is_safe_v2.2`**: production auditor contract with required `risk_score`, `confidence`, `uncertainty`.
- **Evaluators**: `SemanticEvaluator`, `SchemaEvaluator`, `SecurityEvaluator`, `ReleaseGateEvaluator`, `CalibrationEvaluator`.
- **Confusion matrix**: standard layout (TP/FN/FP/TN) with ASCII table in logs.
- **CI**: ruff, black, mypy, pytest + coverage, Python 3.10–3.12 matrix.
- **Benchmark regression**: `scripts/benchmark_gate.py` + nightly workflow.
- **Releases**: GitHub Release on `v*` tags.
- **pre-commit**: ruff, black, whitespace hooks.

## v0.6.0

- Typed `SuiteMetrics`, `RunReport`, leaderboard via `RunReport`.
