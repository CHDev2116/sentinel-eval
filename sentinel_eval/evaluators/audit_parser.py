from sentinel_eval.domain.models import AuditOutput
from sentinel_eval.utils.parsing import audit_json_canonical, parse_audit_response


class AuditParser:
    """Parse raw LLM text into a normalized AuditOutput."""

    def parse(self, raw_output: str) -> tuple[AuditOutput, str]:
        parsed_dict, clean_output = parse_audit_response(raw_output)
        return AuditOutput.from_parsed_dict(parsed_dict), clean_output

    def canonical_json(self, audit: AuditOutput) -> str:
        return audit_json_canonical(audit.model_dump())
