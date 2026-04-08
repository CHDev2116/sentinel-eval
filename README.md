# Red Team Project: Logic Isolation + ROUGE Evaluation

This project evaluates whether an LLM can resist prompt injection signals embedded inside email threads.
It runs batch test cases, parses structured JSON outputs, validates schema quality, computes ROUGE scores, and writes a report.

## Quick Start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install langchain-ollama rouge-score
ollama list | rg gemma4:latest || ollama pull gemma4:latest
python main.py
```

## What This Project Does

- Sends adversarial/normal email threads to an Ollama-backed model.
- Forces a structured audit response:
  - `is_inclusive` (bool)
  - `reasoning` (str)
  - `security_status` (str)
- Cleans and parses model output (including markdown code fences).
- Validates response schema with strict checks.
- Computes ROUGE-1/2/L against `reference_answer`.
- Compares predicted vs expected label (`expected_is_inclusive`).
- Exports detailed batch results to `reports/evaluation_results.json`.

## Project Structure

- `main.py` - Batch pipeline runner.
- `core/logic_isolation_test.py` - LLM prompt + inference wrapper (`SentinelTester`).
- `core/response_utils.py` - Output normalization, JSON extraction, schema validation.
- `core/ROUGE_scores.py` - Unified ROUGE scoring utilities.
- `core/aligned_single_case_demo.py` - Single-case aligned demo.
- `core/generated_case_pipeline_demo.py` - Generated red-team case + project-aligned audit demo.
- `core/async_tri_agent_demo.py` - Async tri-agent (generate/audit/judge) pipeline demo.
- `payloads/email_scenarios.json` - Batch test cases.
- `reports/evaluation_results.json` - Generated evaluation report.

## Requirements

- Python 3.10+ (project currently uses Python 3.13 in `.venv`).
- [Ollama](https://ollama.com/) running locally.
- A local model available in Ollama (default: `gemma4:latest`).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install langchain-ollama rouge-score
```

If you have not pulled the default model yet:

```bash
ollama pull gemma4:latest
```

## Run Batch Evaluation

```bash
python main.py
```

The pipeline prints per-case:

- Raw model response
- Parsed audit JSON
- Schema validation result
- ROUGE metrics
- Label match (`expected_is_inclusive` vs prediction)

It also writes:

- `reports/evaluation_results.json`

## Run Single-Case Demo

```bash
python core/aligned_single_case_demo.py
```

This script demonstrates two aligned PoCs:

- Injection-style email
- Benign project email

Both use the same parsing/validation/scoring pipeline as `main.py`.

## Run Generated-Case Demo

```bash
python core/generated_case_pipeline_demo.py
```

This demo:

- Generates one controlled phishing-style sample for security testing.
- Sends that sample through `SentinelTester` (same audit path as the project).
- Parses and validates output with the existing schema:
  - `is_inclusive`
  - `reasoning`
  - `security_status`
- Appends generated cases into `payloads/email_scenarios.json`.

### Generated-Case CLI Options

```bash
python core/generated_case_pipeline_demo.py \
  --count 3 \
  --generator-model gemma4:latest \
  --target-model gemma4:latest \
  --payload-path payloads/email_scenarios.json
```

- `--count`: Number of generated test cases (minimum effective value is 1).
- `--generator-model`: Model for phishing-style sample generation.
- `--target-model`: Model used by `SentinelTester` for audit.
- `--payload-path`: JSON payload file to append generated cases.

## Run Tests

```bash
python -m unittest tests/test_generated_case_pipeline_demo.py
python -m unittest tests/test_async_tri_agent_demo.py
```

## Run Async Tri-Agent Demo

```bash
python core/async_tri_agent_demo.py \
  --count 5 \
  --concurrency 2 \
  --generator-model gemma4:latest \
  --auditor-model llama3.1:latest \
  --judge-model gemma4:latest
```

This demo runs a 3-step async workflow:

- Generate phishing-style simulation text (for security testing).
- Audit with project-aligned schema (`is_inclusive`, `reasoning`, `security_status`).
- Judge audit quality (`score`, `reason`).

Reports are written to:

- `reports/async_runs/*.jsonl`
- `reports/async_latest.jsonl`

## Test Case Format

Each case in `payloads/email_scenarios.json` should look like:

```json
{
  "case_id": "TC-EXAMPLE",
  "description": "What this case tests",
  "email_thread": "Email content to audit",
  "reference_answer": "{\"is_inclusive\": true, \"reasoning\": \"...\", \"security_status\": \"Pass\"}",
  "expected_is_inclusive": true
}
```

Notes:

- `reference_answer` is used for ROUGE comparison.
- `expected_is_inclusive` is used for correctness matching.

## Interpreting Results

- `schema_validation.is_valid = false` means model output did not satisfy required schema.
- `prediction_match = false` means model classification disagrees with expected label.
- High ROUGE does not guarantee security correctness by itself; use it together with schema + label match.

## Common Issues

- `ModuleNotFoundError: langchain_ollama`
  - Install dependency in `.venv`: `pip install langchain-ollama`
- Ollama connection/model errors
  - Ensure Ollama is running and model exists (`ollama list`)
- JSON parse errors in payload file
  - Keep `payloads/email_scenarios.json` as valid JSON (double quotes, no trailing commas)

## Next Improvements (Optional)

- Add per-case pass/fail policy combining schema + label + threshold metrics.
- Add unit tests for `response_utils.py`.
- Add CLI args for model name and payload path.
