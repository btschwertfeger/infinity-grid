# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Adapters for external services.

This module provides adapters for various external services used by the
Infinity Grid Bot, including exchange APIs and notification services.
"""

from infinity_grid.adapters.exchange_registry import ExchangeAdapterRegistry

# Register exchanges with lazy loading to avoid import errors when optional
# dependencies (extras) are not installed.
ExchangeAdapterRegistry.register_lazy(
    exchange_name="Kraken",
    module_path="infinity_grid.adapters.exchanges.kraken",
    rest_class_name="KrakenExchangeRESTServiceAdapter",
    websocket_class_name="KrakenExchangeWebsocketServiceAdapter",
)

__all__ = ["ExchangeAdapterRegistry"]
