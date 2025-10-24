# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Tests for the Exchange Adapter Registry."""

from typing import Self
from unittest.mock import MagicMock

import pytest

from infinity_grid.adapters import ExchangeAdapterRegistry
from infinity_grid.adapters.exchange_registry import _LazyAdapter
from infinity_grid.interfaces.exchange import (
    IExchangeRESTService,
    IExchangeWebSocketService,
)

EXCHANGES = ("Kraken",)  # needs to be extended when more exchanges are added


class TestExchangeAdapterRegistry:
    """Tests for the ExchangeAdapterRegistry class."""

    @pytest.mark.parametrize("exchange_name", EXCHANGES)
    def test_adapters_registered(self: Self, exchange_name: str) -> None:
        """Test that Kraken adapters are automatically registered."""
        assert exchange_name in ExchangeAdapterRegistry.get_supported_exchanges()

    @pytest.mark.parametrize("exchange_name", EXCHANGES)
    def test_get_rest_adapter(self: Self, exchange_name: str) -> None:
        """Test getting a REST adapter."""
        adapter = ExchangeAdapterRegistry.get_rest_adapter(exchange_name)
        assert adapter is not None
        assert issubclass(adapter, IExchangeRESTService)

    @pytest.mark.parametrize("exchange_name", EXCHANGES)
    def test_get_websocket_adapter(self: Self, exchange_name: str) -> None:
        """Test getting a WebSocket adapter."""
        adapter = ExchangeAdapterRegistry.get_websocket_adapter(exchange_name)
        assert adapter is not None
        assert issubclass(adapter, IExchangeWebSocketService)

    def test_unsupported_exchange_rest(self: Self) -> None:
        """Test that requesting an unsupported exchange raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported exchange for REST adapter"):
            ExchangeAdapterRegistry.get_rest_adapter("UnsupportedExchange")

    def test_unsupported_exchange_websocket(self: Self) -> None:
        """Test that requesting an unsupported exchange raises ValueError."""
        with pytest.raises(
            ValueError,
            match="Unsupported exchange for WebSocket adapter",
        ):
            ExchangeAdapterRegistry.get_websocket_adapter("UnsupportedExchange")

    def test_get_supported_exchanges(self: Self) -> None:
        """Test getting the list of supported exchanges."""
        exchanges = ExchangeAdapterRegistry.get_supported_exchanges()
        assert isinstance(exchanges, list)
        assert "Kraken" in exchanges
        assert len(exchanges) >= 1


class TestLazyLoading:
    """Tests for lazy loading functionality of the registry."""

    def test_lazy_adapter_initialization(self: Self) -> None:
        """Test that LazyAdapter can be initialized without importing."""
        lazy = _LazyAdapter(
            "infinity_grid.adapters.exchanges.kraken",
            "KrakenExchangeRESTServiceAdapter",
            "KrakenExchangeWebsocketServiceAdapter",
        )
        # Testing internal state is acceptable in unit tests
        assert lazy._rest_adapter is None
        assert lazy._websocket_adapter is None

    def test_lazy_adapter_loads_on_demand(self: Self) -> None:
        """Test that adapters are loaded only when requested."""
        lazy = _LazyAdapter(
            "infinity_grid.adapters.exchanges.kraken",
            "KrakenExchangeRESTServiceAdapter",
            "KrakenExchangeWebsocketServiceAdapter",
        )

        # First call should load and cache
        rest_adapter = lazy.get_rest_adapter()
        assert rest_adapter is not None
        assert lazy._rest_adapter is not None
        assert issubclass(rest_adapter, IExchangeRESTService)

        # Second call should return cached version
        rest_adapter_2 = lazy.get_rest_adapter()
        assert rest_adapter_2 is rest_adapter

    def test_lazy_adapter_websocket_loads_on_demand(self: Self) -> None:
        """Test that WebSocket adapters are loaded only when requested."""
        lazy = _LazyAdapter(
            "infinity_grid.adapters.exchanges.kraken",
            "KrakenExchangeRESTServiceAdapter",
            "KrakenExchangeWebsocketServiceAdapter",
        )

        ws_adapter = lazy.get_websocket_adapter()
        assert ws_adapter is not None
        assert lazy._websocket_adapter is not None
        assert issubclass(ws_adapter, IExchangeWebSocketService)

    def test_lazy_registration(self: Self) -> None:
        """Test lazy registration of exchange adapters."""
        # Save and restore registry state to avoid side effects
        original_adapters = ExchangeAdapterRegistry._adapters.copy()

        try:
            ExchangeAdapterRegistry.register_lazy(
                "TestExchange",
                "infinity_grid.adapters.exchanges.kraken",
                "KrakenExchangeRESTServiceAdapter",
                "KrakenExchangeWebsocketServiceAdapter",
            )

            assert "TestExchange" in ExchangeAdapterRegistry.get_supported_exchanges()
            adapter = ExchangeAdapterRegistry._adapters["TestExchange"]
            assert isinstance(adapter, _LazyAdapter)

        finally:
            # Restore original state
            ExchangeAdapterRegistry._adapters = original_adapters

    def test_lazy_adapter_import_error(self: Self) -> None:
        """Test that ImportError is raised with helpful message when module fails to load."""
        # Save and restore registry state to avoid side effects
        original_adapters = ExchangeAdapterRegistry._adapters.copy()

        try:
            ExchangeAdapterRegistry.register_lazy(
                "FakeExchange",
                "non_existent_module",
                "FakeRESTAdapter",
                "FakeWSAdapter",
            )

            with pytest.raises(ImportError, match="Failed to load REST adapter"):
                ExchangeAdapterRegistry.get_rest_adapter("FakeExchange")

            with pytest.raises(ImportError, match="Failed to load WebSocket adapter"):
                ExchangeAdapterRegistry.get_websocket_adapter("FakeExchange")

        finally:
            # Restore original state
            ExchangeAdapterRegistry._adapters = original_adapters

    def test_eager_registration(self: Self) -> None:
        """Test eager registration still works for non-optional dependencies."""
        # Create mock adapters
        mock_rest = MagicMock(spec=IExchangeRESTService)
        mock_ws = MagicMock(spec=IExchangeWebSocketService)

        # Save and restore registry state to avoid side effects
        original_adapters = ExchangeAdapterRegistry._adapters.copy()

        try:
            ExchangeAdapterRegistry.register(
                "EagerExchange",
                mock_rest,
                mock_ws,
            )

            assert "EagerExchange" in ExchangeAdapterRegistry.get_supported_exchanges()
            adapter = ExchangeAdapterRegistry._adapters["EagerExchange"]
            assert isinstance(adapter, tuple)
            assert adapter[0] is mock_rest
            assert adapter[1] is mock_ws

            # Verify we can retrieve them
            assert (
                ExchangeAdapterRegistry.get_rest_adapter("EagerExchange") is mock_rest
            )
            assert (
                ExchangeAdapterRegistry.get_websocket_adapter("EagerExchange")
                is mock_ws
            )

        finally:
            # Restore original state
            ExchangeAdapterRegistry._adapters = original_adapters

    def test_kraken_uses_lazy_loading(self: Self) -> None:
        """Test that Kraken is registered with lazy loading."""
        adapter = ExchangeAdapterRegistry._adapters.get("Kraken")
        assert adapter is not None
        assert isinstance(
            adapter,
            _LazyAdapter,
        ), "Kraken should use lazy loading for optional dependency"
