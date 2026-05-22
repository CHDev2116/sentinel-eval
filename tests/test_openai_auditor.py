import json
import unittest
from unittest.mock import MagicMock, patch

from sentinel_eval.clients.openai_compatible import OpenAICompatibleAuditor
from sentinel_eval.clients.protocol import ModelInferenceParams


class TestOpenAICompatibleAuditor(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_chat_completion_parses_response(self, mock_urlopen):
        payload = {
            "choices": [{"message": {"content": '{"is_safe": true, "reasoning": "ok"}'}}],
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        auditor = OpenAICompatibleAuditor(
            model_name="test-model",
            api_base="http://localhost:9999/v1",
            api_key="sk-test",
            cache=None,
            inference_params=ModelInferenceParams(temperature=0.0),
        )
        result = auditor.audit("hello thread")
        self.assertIn("is_safe", result.raw_output)
        self.assertEqual(result.backend, "openai_compatible")


if __name__ == "__main__":
    unittest.main()
