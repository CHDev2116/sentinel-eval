# Contributing

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Checks (match CI)

```bash
ruff check sentinel_eval tests examples scripts
ruff format --check sentinel_eval tests examples scripts
black --check sentinel_eval tests examples scripts
mypy sentinel_eval
pytest
python scripts/benchmark_gate.py
```

## Prompt versions

- Current auditor prompt: `is_safe_v2.2` (`sentinel_eval/prompts/audit.py`)
- Bump `PROMPT_VERSION` and document changes in GitHub Releases when behavior changes.

## Releases

```bash
git tag v0.7.0
git push origin v0.7.0
```

The release workflow runs tests and publishes GitHub Release notes.
