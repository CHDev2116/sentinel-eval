import json
import re

AUDIT_KEYS = ("is_safe", "reasoning", "security_status")
LEGACY_SAFE_KEY = "is_inclusive"


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


def _normalize_safe_flag(loaded):
    """Map is_safe or legacy is_inclusive to is_safe."""
    if isinstance(loaded, dict):
        if "is_safe" in loaded:
            return _coerce_bool(loaded.get("is_safe"))
        if LEGACY_SAFE_KEY in loaded:
            return _coerce_bool(loaded.get(LEGACY_SAFE_KEY))
    return None


def parse_audit_response(raw_output):
    """
    Parse model output into a normalized dict.

    Returns:
        tuple[dict, str]
        - parsed object with guaranteed keys (is_safe, reasoning, security_status)
        - cleaned output string used for parsing
    """
    clean_output = normalize_model_output(raw_output)
    json_text = extract_json_text(clean_output)

    parsed = {
        "is_safe": None,
        "reasoning": "",
        "security_status": "ParseError",
    }
    try:
        loaded = json.loads(json_text)
        parsed["is_safe"] = _normalize_safe_flag(loaded)
        parsed["reasoning"] = str(loaded.get("reasoning", "")).strip()
        parsed["security_status"] = (
            str(loaded.get("security_status", "")).strip() or "Unknown"
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        parsed["reasoning"] = "Model output could not be parsed as valid JSON."

    return parsed, clean_output


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
