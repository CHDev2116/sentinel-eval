# Changelog

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
