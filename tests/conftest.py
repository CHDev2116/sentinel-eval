"""Pytest: skip optional integration tests unless extras installed."""

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: needs langchain-ollama or live services",
    )


def pytest_collection_modifyitems(config, items):
    try:
        import langchain_ollama  # noqa: F401
    except ImportError:
        skip = pytest.mark.skip(reason="pip install -e '.[demos]' for integration tests")
        for item in items:
            if "generated_case_pipeline" in item.nodeid or "async_tri_agent" in item.nodeid:
                item.add_marker(skip)
