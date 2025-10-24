# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Exchange Adapter Registry

This module provides a centralized registry for managing exchange adapters.
It follows the Registry pattern to decouple exchange adapter selection from
the strategy implementation, making it easy to add new exchanges without
modifying core strategy code.

Supports lazy loading for optional exchange dependencies:
    # Register an adapter with lazy loading (for optional extras)
    ExchangeAdapterRegistry.register_lazy(
        "Kraken",
        "infinity_grid.adapters.exchanges.kraken",
        "KrakenExchangeRESTServiceAdapter",
        "KrakenExchangeWebsocketServiceAdapter"
    )

    # Get adapters for an exchange (imported only when needed)
    rest_adapter = ExchangeAdapterRegistry.get_rest_adapter("Kraken")
    ws_adapter = ExchangeAdapterRegistry.get_websocket_adapter("Kraken")
"""

from importlib import import_module
from logging import getLogger
from typing import ClassVar, Self

from infinity_grid.interfaces.exchange import (
    IExchangeRESTService,
    IExchangeWebSocketService,
)

LOG = getLogger(__name__)


class _LazyAdapter:
    """
    Lazy loader for exchange adapters.

    Defers importing the adapter module until it's actually needed,
    allowing optional dependencies to be registered without being imported.
    """

    def __init__(
        self: Self,
        module_path: str,
        rest_class_name: str,
        websocket_class_name: str,
    ) -> None:
        self.module_path = module_path
        self.rest_class_name = rest_class_name
        self.websocket_class_name = websocket_class_name
        self._rest_adapter: type[IExchangeRESTService] | None = None
        self._websocket_adapter: type[IExchangeWebSocketService] | None = None

    def get_rest_adapter(self: Self) -> type[IExchangeRESTService]:
        """Load and return the REST adapter."""
        if self._rest_adapter is None:
            module = import_module(self.module_path)
            self._rest_adapter = getattr(module, self.rest_class_name)
        return self._rest_adapter

    def get_websocket_adapter(self: Self) -> type[IExchangeWebSocketService]:
        """Load and return the WebSocket adapter."""
        if self._websocket_adapter is None:
            module = import_module(self.module_path)
            self._websocket_adapter = getattr(module, self.websocket_class_name)
        return self._websocket_adapter


class ExchangeAdapterRegistry:
    """
    Registry for exchange adapters.

    Provides centralized management of REST and WebSocket adapters for
    different exchanges. New exchanges can be registered without modifying
    existing code.

    Supports both eager and lazy registration for handling optional dependencies.
    """

    _adapters: ClassVar[
        dict[
            str,
            _LazyAdapter
            | tuple[type[IExchangeRESTService], type[IExchangeWebSocketService]],
        ]
    ] = {}

    @classmethod
    def register(
        cls: type[Self],
        exchange_name: str,
        rest_adapter: type[IExchangeRESTService],
        websocket_adapter: type[IExchangeWebSocketService],
    ) -> None:
        """
        Register adapters for an exchange (eager loading).

        Use this when the exchange dependencies are always available.

        :param exchange_name: The name of the exchange (e.g., "Kraken")
        :type exchange_name: str
        :param rest_adapter: The REST API adapter class
        :type rest_adapter: type[IExchangeRESTService]
        :param websocket_adapter: The WebSocket adapter class
        :type websocket_adapter: type[IExchangeWebSocketService]
        """
        LOG.debug("Registering adapters for exchange: %s", exchange_name)
        cls._adapters[exchange_name] = (rest_adapter, websocket_adapter)

    @classmethod
    def register_lazy(
        cls: type[Self],
        exchange_name: str,
        module_path: str,
        rest_class_name: str,
        websocket_class_name: str,
    ) -> None:
        """
        Register adapters for an exchange (lazy loading).

        Use this for optional exchange dependencies (extras) to avoid
        import errors when the dependency isn't installed.

        :param exchange_name: The name of the exchange (e.g., "Kraken")
        :type exchange_name: str
        :param module_path: The module path containing the adapters
        :type module_path: str
        :param rest_class_name: The name of the REST adapter class
        :type rest_class_name: str
        :param websocket_class_name: The name of the WebSocket adapter class
        :type websocket_class_name: str
        """
        LOG.debug("Lazy registering adapters for exchange: %s", exchange_name)
        cls._adapters[exchange_name] = _LazyAdapter(
            module_path,
            rest_class_name,
            websocket_class_name,
        )

    @classmethod
    def get_rest_adapter(
        cls: type[Self],
        exchange_name: str,
    ) -> type[IExchangeRESTService]:
        """
        Get the REST adapter for an exchange.

        :param exchange_name: The name of the exchange
        :type exchange_name: str
        :return: The REST adapter class
        :rtype: type[IExchangeRESTService]
        :raises ValueError: If the exchange is not registered
        :raises ImportError: If the exchange module cannot be imported
        """
        if exchange_name not in cls._adapters:
            raise ValueError(
                f"Unsupported exchange for REST adapter: {exchange_name}. "
                f"Available exchanges: {', '.join(cls._adapters.keys())}",
            )

        adapter = cls._adapters[exchange_name]
        if isinstance(adapter, _LazyAdapter):
            try:
                return adapter.get_rest_adapter()
            except (ImportError, AttributeError) as exc:
                raise ImportError(
                    f"Failed to load REST adapter for {exchange_name}. "
                    f"Make sure the required dependencies are installed. "
                    f"e.g. for Kraken, install with: pip install infinity-grid[kraken]",
                ) from exc
        return adapter[0]

    @classmethod
    def get_websocket_adapter(
        cls: type[Self],
        exchange_name: str,
    ) -> type[IExchangeWebSocketService]:
        """
        Get the WebSocket adapter for an exchange.

        :param exchange_name: The name of the exchange
        :type exchange_name: str
        :return: The WebSocket adapter class
        :rtype: type[IExchangeWebSocketService]
        :raises ValueError: If the exchange is not registered
        :raises ImportError: If the exchange module cannot be imported
        """
        if exchange_name not in cls._adapters:
            raise ValueError(
                f"Unsupported exchange for WebSocket adapter: {exchange_name}. "
                f"Available exchanges: {', '.join(cls._adapters.keys())}",
            )

        adapter = cls._adapters[exchange_name]
        if isinstance(adapter, _LazyAdapter):
            try:
                return adapter.get_websocket_adapter()
            except (ImportError, AttributeError) as exc:
                raise ImportError(
                    f"Failed to load WebSocket adapter for {exchange_name}. "
                    f"Make sure the required dependencies are installed. "
                    f"For Kraken, install with: pip install infinity-grid[kraken]",
                ) from exc
        return adapter[1]

    @classmethod
    def get_supported_exchanges(cls: type[Self]) -> list[str]:
        """
        Get a list of all supported exchanges.

        :return: List of exchange names
        :rtype: list[str]
        """
        return list(cls._adapters.keys())
