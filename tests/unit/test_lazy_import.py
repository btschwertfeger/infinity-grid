# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Tests to verify that the package can be imported without optional dependencies.

This test file verifies that the lazy loading mechanism works correctly,
allowing the package to be imported even when optional extras (like Kraken)
are not installed.
"""

from types import ModuleType
from unittest.mock import patch

import pytest


def test_package_imports_without_kraken_sdk() -> None:
    """
    Test that infinity_grid.adapters can be imported without kraken-sdk
    installed.

    This simulates the scenario where a user has not installed the Kraken extra
    but still wants to use other parts of the package or check supported
    exchanges.
    """
    from infinity_grid.adapters import ExchangeAdapterRegistry
    from infinity_grid.adapters.exchange_registry import _LazyAdapter

    # Kraken is registered via lazy loading
    assert "Kraken" in ExchangeAdapterRegistry.get_supported_exchanges()

    # Get the Kraken adapter and clear its cache to force a fresh import
    kraken_adapter = ExchangeAdapterRegistry._adapters["Kraken"]
    assert isinstance(kraken_adapter, _LazyAdapter)
    kraken_adapter._rest_adapter = None
    kraken_adapter._websocket_adapter = None

    # Mock importlib.import_module to simulate kraken not being installed
    def mock_import_module(name: str) -> ModuleType:
        if "kraken" in name.lower():
            raise ImportError(f"No module named '{name}'")
        # For any other module, use the real import
        import importlib

        return importlib.import_module(name)

    # Use of python-kraken-sdk must raise ImportError
    with patch(
        "infinity_grid.adapters.exchange_registry.import_module",
        side_effect=mock_import_module,
    ):
        with pytest.raises(
            ImportError,
            match="Failed to load REST adapter for Kraken",
        ):
            ExchangeAdapterRegistry.get_rest_adapter("Kraken")

        # Reset cache again for websocket test
        kraken_adapter._websocket_adapter = None

        with pytest.raises(
            ImportError,
            match="Failed to load WebSocket adapter for Kraken",
        ):
            ExchangeAdapterRegistry.get_websocket_adapter("Kraken")


def test_registry_shows_all_exchanges_without_importing() -> None:
    """
    Test that get_supported_exchanges works without importing exchange modules.

    This verifies that we can list all registered exchanges without triggering
    the import of optional dependencies.
    """
    from infinity_grid.adapters import ExchangeAdapterRegistry

    # This should work without importing kraken module
    exchanges = ExchangeAdapterRegistry.get_supported_exchanges()
    assert isinstance(exchanges, list)
    assert "Kraken" in exchanges
