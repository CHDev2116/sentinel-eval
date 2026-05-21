import json
import re

AUDIT_KEYS = ("is_safe", "reasoning", "security_status")
LEGACY_SAFE_KEY = "is_inclusive"

# Ollama structured output (langchain_ollama passes this as format="json" schema when supported).
AUDIT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "is_safe": {"type": "boolean"},
        "reasoning": {"type": "string"},
        "security_status": {"type": "string"},
    },
    "required": ["is_safe", "reasoning", "security_status"],
    "additionalProperties": False,
}


def normalize_model_output(raw_output):
    """Normalize LLM output to a clean string."""
    if raw_output is None:
        return ""
    return str(raw_output).strip()


def _extract_last_json_object(text):
    """Return the last balanced {...} substring, if any."""
    end = text.rfind("}")
    if end == -1:
        return None
    depth = 0
    for i in range(end, -1, -1):
        ch = text[i]
        if ch == "}":
            depth += 1
        elif ch == "{":
            depth -= 1
            if depth == 0:
                return text[i : end + 1].strip()
    return None


def extract_json_text(text):
    """Extract JSON object text, handling markdown code fences."""
    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced_match:
        return fenced_match.group(1).strip()

    balanced = _extract_last_json_object(text)
    if balanced:
        return balanced

    obj_match = re.search(r"\{.*\}", text, re.DOTALL)
    if obj_match:
        return obj_match.group(0).strip()

    return text.strip()


def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return None


def normalize_legacy_field_names(text):
    """Rewrite deprecated JSON keys in model text before parsing."""
    if not text:
        return text
    normalized = text
    for old, new in (
        ('"is_inclusive"', '"is_safe"'),
        ("'is_inclusive'", "'is_safe'"),
    ):
        normalized = normalized.replace(old, new)
    return normalized


def _normalize_loaded_audit(loaded):
    """Drop legacy is_inclusive key; keep is_safe as the single source of truth."""
    if not isinstance(loaded, dict):
        return loaded
    if LEGACY_SAFE_KEY in loaded:
        legacy_value = loaded.pop(LEGACY_SAFE_KEY)
        if "is_safe" not in loaded:
            loaded["is_safe"] = legacy_value
    return loaded


def _normalize_safe_flag(loaded):
    """Read is_safe from a normalized audit object."""
    if isinstance(loaded, dict) and "is_safe" in loaded:
        return _coerce_bool(loaded.get("is_safe"))
    return None


def parse_audit_response(raw_output):
    """
    Parse model output into a normalized dict.

    Returns:
        tuple[dict, str]
        - parsed object with guaranteed keys (is_safe, reasoning, security_status)
        - cleaned output string used for parsing
    """
    clean_output = normalize_legacy_field_names(normalize_model_output(raw_output))
    json_text = extract_json_text(clean_output)

    parsed = {
        "is_safe": None,
        "reasoning": "",
        "security_status": "ParseError",
    }
    try:
        loaded = _normalize_loaded_audit(json.loads(json_text))
        parsed["is_safe"] = _normalize_safe_flag(loaded)
        parsed["reasoning"] = str(loaded.get("reasoning", "")).strip()
        parsed["security_status"] = (
            str(loaded.get("security_status", "")).strip() or "Unknown"
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        parsed["reasoning"] = "Model output could not be parsed as valid JSON."

    canonical_output = audit_json_canonical(parsed)
    return parsed, canonical_output


def audit_json_canonical(parsed_output):
    """Stable JSON string for ROUGE comparison."""
    payload = {
        "is_safe": parsed_output.get("is_safe"),
        "reasoning": parsed_output.get("reasoning", ""),
        "security_status": parsed_output.get("security_status", ""),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ": "))


def validate_audit_schema(parsed_output):
    """Validate strict output schema and return validation metadata."""
    errors = []

    if not isinstance(parsed_output.get("is_safe"), bool):
        errors.append("is_safe must be a boolean.")

    reasoning = parsed_output.get("reasoning")
    if not isinstance(reasoning, str) or not reasoning.strip():
        errors.append("reasoning must be a non-empty string.")

    security_status = parsed_output.get("security_status")
    if not isinstance(security_status, str) or not security_status.strip():
        errors.append("security_status must be a non-empty string.")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
    }
