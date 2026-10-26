"""Ensure the integration can load on the supported Home Assistant runtime."""

import importlib


def test_integration_imports():
    """Catch dependencies that prevent the integration from loading at all."""
    integration = importlib.import_module("custom_components.molekule")
    assert callable(integration.async_setup_entry)
