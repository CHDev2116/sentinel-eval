from typing import Any

from sentinel_eval.domain.models import AuditOutput, SchemaEvalResult
from sentinel_eval.evaluators.protocol import CaseEvalContext
from sentinel_eval.evaluators.schema_validator import SchemaValidator


class SchemaEvaluator:
    """JSON schema / contract validation only."""

    evaluator_id = "schema"

    def __init__(self, validator: SchemaValidator | None = None):
        self.validator = validator or SchemaValidator()

    def evaluate(self, audit: AuditOutput | dict[str, Any]) -> SchemaEvalResult:
        return SchemaEvalResult(validation=self.validator.validate(audit))

    def evaluate_context(self, ctx: CaseEvalContext) -> SchemaEvalResult:
        return self.evaluate(ctx.audit)
