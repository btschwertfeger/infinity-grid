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

import builtins
import sys
from types import ModuleType

import pytest


def test_package_imports_without_kraken_sdk() -> None:
    """
    Test that infinity_grid.adapters can be imported without kraken-sdk installed.

    This simulates the scenario where a user has not installed the Kraken extra
    but still wants to use other parts of the package or check supported exchanges.
    """
    # Mock the kraken module to simulate it not being installed
    original_import = builtins.__import__

    def mock_import(name: str, *args, **kwargs) -> ModuleType:  # noqa: ANN002,ANN003
        if name.startswith("kraken"):
            raise ImportError(f"No module named '{name}'")
        return original_import(name, *args, **kwargs)

    # Temporarily replace the import function
    builtins.__import__ = mock_import

    try:
        # Remove kraken from sys.modules if it's already loaded
        kraken_modules = [key for key in sys.modules if key.startswith("kraken")]
        removed_modules = {}
        for mod in kraken_modules:
            removed_modules[mod] = sys.modules.pop(mod)

        # Also remove infinity_grid.adapters.exchanges.kraken if loaded
        infinity_kraken_modules = [
            key
            for key in sys.modules
            if "infinity_grid.adapters.exchanges.kraken" in key
        ]
        for mod in infinity_kraken_modules:
            removed_modules[mod] = sys.modules.pop(mod)

        # This should work even without python-kraken-sdk
        from infinity_grid.adapters import ExchangeAdapterRegistry

        # Kraken should be registered (lazy loading)
        assert "Kraken" in ExchangeAdapterRegistry.get_supported_exchanges()

        # Trying to use Kraken should raise ImportError with helpful message
        try:
            ExchangeAdapterRegistry.get_rest_adapter("Kraken")
            pytest.fail("Should have raised ImportError")
        except ImportError as exc:
            assert "Failed to load REST adapter for Kraken" in str(exc)  # noqa: PT017
            assert "pip install infinity-grid[kraken]" in str(exc)  # noqa: PT017

    finally:
        # Restore the original import function
        builtins.__import__ = original_import

        # Restore removed modules
        sys.modules.update(removed_modules)


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
