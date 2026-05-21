import unittest
from unittest.mock import MagicMock, patch

from sentinel_eval.clients.ollama_auditor import OllamaAuditor
from sentinel_eval.clients.protocol import ModelInferenceParams
from sentinel_eval.clients.response_cache import ResponseCache
from sentinel_eval.domain.audit_result import AuditResult
from sentinel_eval.evaluators.case_evaluator import _audit_raw_output


class TestAuditorProtocol(unittest.TestCase):
    def test_audit_raw_output_legacy_run_test(self):
        legacy = MagicMock()
        legacy.run_test.return_value = '{"is_safe": true}'
        self.assertEqual(_audit_raw_output(legacy, "thread"), '{"is_safe": true}')

    def test_audit_raw_output_audit_result(self):
        auditor = MagicMock(spec=["audit"])
        auditor.audit.return_value = AuditResult(
            raw_output='{"is_safe": false}',
            model="m",
            prompt_version="p",
        )
        self.assertIn("false", _audit_raw_output(auditor, "thread"))

    @patch("sentinel_eval.clients.ollama_auditor.Client")
    def test_ollama_auditor_uses_cache(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.chat.return_value = {"message": {"content": '{"is_safe": true}'}}
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            cache = ResponseCache(f"{tmp}/c.sqlite3")
            auditor = OllamaAuditor(
                model_name="test-model",
                inference_params=ModelInferenceParams(seed=7),
                cache=cache,
            )
            r1 = auditor.audit("email body")
            r2 = auditor.audit("email body")
        self.assertFalse(r1.cached)
        self.assertTrue(r2.cached)
        mock_client.chat.assert_called_once()


if __name__ == "__main__":
    unittest.main()
