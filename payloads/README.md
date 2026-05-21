# Payloads

| File | Role |
|------|------|
| `scenarios_golden.json` | **Canonical** 12-case benchmark (labels + reference answers) |
| `scenarios_generated.json` | Experimental cases (`needs_review: true`, no auto labels) |

`email_scenarios.json` was removed in v0.2 — it duplicated `scenarios_golden.json`. Use `scenarios_golden.json` only.

Reference answers use `security_status`: **Pass** when `is_safe: true`, **Fail** when `is_safe: false` (aligned with `sentinel_eval.prompts.audit` few-shot examples).
