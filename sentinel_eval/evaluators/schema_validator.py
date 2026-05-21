from typing import Any

from sentinel_eval.config import get_settings
from sentinel_eval.domain.models import AuditOutput, SchemaValidationResult
from sentinel_eval.schemas.audit import validate_audit_schema


class SchemaValidator:
    """Strict JSON contract validation for auditor outputs."""

    def __init__(self, require_calibration: bool | None = None):
        settings = get_settings()
        self.require_calibration = (
            require_calibration
            if require_calibration is not None
            else settings.require_calibration_fields
        )

    def validate(self, audit: AuditOutput | dict[str, Any]) -> SchemaValidationResult:
        payload = audit.model_dump() if isinstance(audit, AuditOutput) else audit
        raw = validate_audit_schema(payload, require_calibration=self.require_calibration)
        return SchemaValidationResult.model_validate(raw)
