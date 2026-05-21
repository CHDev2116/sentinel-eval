AUDIT_KEYS = ("is_safe", "reasoning", "security_status")
CALIBRATION_KEYS = ("risk_score", "confidence", "uncertainty")
LEGACY_SAFE_KEY = "is_inclusive"

AUDIT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "is_safe": {"type": "boolean"},
        "reasoning": {"type": "string"},
        "security_status": {"type": "string"},
        "risk_score": {"type": "number", "minimum": 0, "maximum": 1},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "uncertainty": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["is_safe", "reasoning", "security_status"],
    "additionalProperties": False,
}


def _validate_calibration_field(parsed_output: dict, key: str, errors: list[str], *, required: bool) -> None:
    if key not in parsed_output or parsed_output.get(key) is None:
        if required:
            errors.append(f"{key} is required (prompt is_safe_v2.2+).")
        return
    value = parsed_output.get(key)
    try:
        num = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        errors.append(f"{key} must be a number between 0 and 1.")
        return
    if num < 0 or num > 1:
        errors.append(f"{key} must be between 0 and 1.")


def validate_audit_schema(parsed_output, *, require_calibration: bool = False):
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
    elif security_status.strip() not in ("Pass", "Fail"):
        errors.append('security_status must be exactly "Pass" or "Fail".')

    for key in CALIBRATION_KEYS:
        _validate_calibration_field(parsed_output, key, errors, required=require_calibration)

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
    }
