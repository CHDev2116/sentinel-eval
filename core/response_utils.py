import json
import re


def normalize_model_output(raw_output):
    """Normalize LLM output to a clean string."""
    if raw_output is None:
        return ""
    return str(raw_output).strip()


def extract_json_text(text):
    """Extract JSON object text, handling markdown code fences."""
    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced_match:
        return fenced_match.group(1).strip()

    obj_match = re.search(r"\{.*\}", text, re.DOTALL)
    if obj_match:
        return obj_match.group(0).strip()

    return text.strip()


def parse_audit_response(raw_output):
    """
    Parse model output into a normalized dict.

    Returns:
        tuple[dict, str]
        - parsed object with guaranteed keys
        - cleaned output string used for parsing
    """
    clean_output = normalize_model_output(raw_output)
    json_text = extract_json_text(clean_output)

    parsed = {
        "is_inclusive": None,
        "reasoning": "",
        "security_status": "ParseError",
    }
    try:
        loaded = json.loads(json_text)
        parsed["is_inclusive"] = loaded.get("is_inclusive")
        parsed["reasoning"] = str(loaded.get("reasoning", "")).strip()
        parsed["security_status"] = (
            str(loaded.get("security_status", "")).strip() or "Unknown"
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        parsed["reasoning"] = "Model output could not be parsed as valid JSON."

    return parsed, clean_output


def validate_audit_schema(parsed_output):
    """Validate strict output schema and return validation metadata."""
    errors = []

    if not isinstance(parsed_output.get("is_inclusive"), bool):
        errors.append("is_inclusive must be a boolean.")

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
