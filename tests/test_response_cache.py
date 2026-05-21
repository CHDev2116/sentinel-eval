import tempfile
import unittest

from sentinel_eval.clients.protocol import ModelInferenceParams
from sentinel_eval.clients.response_cache import ResponseCache, audit_cache_key


class TestResponseCache(unittest.TestCase):
    def test_roundtrip_and_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = ResponseCache(f"{tmp}/cache.sqlite3", enabled=True)
            key = audit_cache_key(
                backend="ollama",
                model="m",
                prompt_sha256="abc",
                thread="hello",
                inference=ModelInferenceParams(temperature=0.0, seed=42),
            )
            self.assertIsNone(cache.get(key))
            cache.set(key, '{"is_safe": true}')
            self.assertEqual(cache.get(key), '{"is_safe": true}')
            stats = cache.stats()
            self.assertEqual(stats["hits"], 1)
            self.assertEqual(stats["misses"], 1)
            cache.close()

    def test_cache_key_changes_with_inference(self):
        base = dict(
            backend="ollama",
            model="m",
            prompt_sha256="p",
            thread="t",
        )
        k1 = audit_cache_key(**base, inference=ModelInferenceParams(seed=1))
        k2 = audit_cache_key(**base, inference=ModelInferenceParams(seed=2))
        self.assertNotEqual(k1, k2)


if __name__ == "__main__":
    unittest.main()
