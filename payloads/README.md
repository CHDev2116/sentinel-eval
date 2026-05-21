# Benchmark payloads (versioned)

Datasets are versioned for **eval reproducibility**. Each suite ships a `manifest.json` plus a cases file.

## Layout

```
payloads/
  v1/          # deprecated placeholder
  v2/          # canonical golden-12 (dataset_version v2.1)
  generated/   # experimental LLM-generated cases (gen-0.1)
  mutations/   # mutation-stress-10 (mut-1.0, per-case mutation_kinds)
```

## Golden (`v2`)

| File | Role |
|------|------|
| `v2/manifest.json` | `dataset_version`, suite id, `cases_file`, compatible prompts |
| `v2/scenarios_golden.json` | Envelope: `{ "dataset_version": "v2.1", "cases": [...] }` |

CLI shortcuts: `--payload v2`, `--payload v2.1`, or `--payload golden`.

## Generated (`generated/`)

| File | Role |
|------|------|
| `generated/manifest.json` | Dataset metadata |
| `generated/scenarios.json` | Envelope with generated cases |

Enable with `sentinel-eval --include-generated`.

## Mutations (`mutations/`)

| File | Role |
|------|------|
| `mutations/manifest.json` | Suite `mutation-stress-10`, compatible with v2.2 / v3.0 |
| `mutations/scenarios_mutation.json` | Each case may include `mutation_kinds` (applied automatically on run) |

CLI: `--payload mutations` (aliases: `mutation`, `mut`). Recommended:

```bash
sentinel-eval --all --payload mutations --prompt is_safe_v3.0 --judge-ensemble
```

Regression floors (optional): `benchmarks/mutations_thresholds.json` (`ensemble_pass_pct`, etc.).

## Conventions

- Reference answers use `security_status`: `"Pass"` (safe) / `"Fail"` (unsafe).
- Align auditor prompt with `compatible_prompts` in the manifest (currently `is_safe_v2.2`).
- Do not duplicate golden data under new flat filenames; bump `dataset_version` in `v2/` instead.
