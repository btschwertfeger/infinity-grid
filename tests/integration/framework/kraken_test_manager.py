# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Kraken-specific implementation of the integration testing framework.

This module demonstrates how to implement the exchange-agnostic testing
framework for a specific exchange (Kraken), showing the pattern that
should be followed for other exchanges.
"""

import logging
from typing import Any, Dict, List

from infinity_grid.models.configuration import (
    BotConfigDTO,
    DBConfigDTO,
    NotificationConfigDTO,
)

from ..framework.base_test_manager import BaseIntegrationTestManager, MockExchangeAPI

LOG = logging.getLogger(__name__)


class KrakenExchangeConfig:
    """Kraken-specific exchange configuration."""

    def __init__(
        self,
        base_currency: str,
        quote_currency: str,
        pair: str,
        ws_symbol: str,
    ) -> None:
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.pair = pair
        self.ws_symbol = ws_symbol


class KrakenMockAPI:
    """
    Kraken-specific mock API implementation.

    This replaces the previous KrakenAPI mock class but implements
    the standardized MockExchangeAPI protocol.
    """

    def __init__(self, config: KrakenExchangeConfig) -> None:
        self.config = config
        self._open_orders: List[Dict[str, Any]] = []
        self._balances: Dict[str, Dict[str, float]] = {
            config.base_currency: {"balance": 0.0, "hold_trade": 0.0},
            config.quote_currency: {"balance": 10000.0, "hold_trade": 0.0},
        }
        self._order_counter = 0

    def setup_initial_state(self) -> None:
        """Setup initial state for testing."""
        self._open_orders.clear()
        self._balances = {
            self.config.base_currency: {"balance": 0.0, "hold_trade": 0.0},
            self.config.quote_currency: {"balance": 10000.0, "hold_trade": 0.0},
        }

    def simulate_ticker_update(self, price: float) -> Dict[str, Any]:
        """Simulate a ticker price update."""
        return {
            "channel": "ticker",
            "type": "update",
            "data": [
                {
                    "symbol": self.config.ws_symbol,
                    "bid": price - 0.5,
                    "ask": price + 0.5,
                    "last": price,
                    "volume": 1000.0,
                },
            ],
        }

    def simulate_order_fill(self, order_id: str) -> Dict[str, Any]:
        """Simulate an order being filled."""
        # Find and remove the order
        order = next((o for o in self._open_orders if o["id"] == order_id), None)
        if order:
            self._open_orders.remove(order)

            # Update balances
            if order["side"] == "buy":
                cost = float(order["price"]) * float(order["volume"])
                self._balances[self.config.quote_currency]["balance"] -= cost
                self._balances[self.config.base_currency]["balance"] += float(
                    order["volume"],
                )
            else:  # sell
                proceeds = float(order["price"]) * float(order["volume"])
                self._balances[self.config.base_currency]["balance"] -= float(
                    order["volume"],
                )
                self._balances[self.config.quote_currency]["balance"] += proceeds

        return {
            "channel": "ownTrades",
            "type": "update",
            "data": (
                [
                    {
                        "ordertxid": order_id,
                        "trade_id": f"trade_{self._order_counter}",
                        "side": order["side"],
                        "vol": order["volume"],
                        "price": order["price"],
                    },
                ]
                if order
                else []
            ),
        }

    def get_open_orders(self) -> List[Dict[str, Any]]:
        """Get currently open orders."""
        return self._open_orders.copy()

    def get_balances(self) -> Dict[str, Dict[str, float]]:
        """Get current balances."""
        return self._balances.copy()

    def add_order(
        self,
        side: str,
        price: float,
        volume: float,
    ) -> str:
        """Add a new order to the mock orderbook."""
        self._order_counter += 1
        order_id = f"order_{self._order_counter}"

        order = {
            "id": order_id,
            "side": side,
            "price": str(price),
            "volume": str(volume),
            "pair": self.config.pair,
        }
        self._open_orders.append(order)
        return order_id


class KrakenIntegrationTestManager(BaseIntegrationTestManager):
    """
    Kraken-specific integration test manager.

    This class demonstrates how to implement the exchange-agnostic
    framework for Kraken exchange.
    """

    def __init__(
        self,
        bot_config: BotConfigDTO,
        notification_config: NotificationConfigDTO,
        db_config: DBConfigDTO,
        exchange_config: KrakenExchangeConfig,
    ) -> None:
        super().__init__(bot_config, notification_config, db_config, exchange_config)
        self._kraken_config = exchange_config

    async def initialize_engine(self) -> None:
        """Initialize the BotEngine with Kraken-specific adapters."""
        from ..kraken_exchange.helper import get_kraken_instance

        # Use the existing helper function but adapt to new structure
        self._engine, kraken_api = await get_kraken_instance(
            bot_config=self.bot_config,
            notification_config=self._notification_config,
            db_config=self._db_config,
            kraken_config=self._kraken_config,
        )

        # Wrap the existing KrakenAPI in our new interface
        self._mock_api = KrakenMockAPI(self._kraken_config)

    def create_mock_api(self) -> MockExchangeAPI:
        """Create Kraken-specific mock API."""
        return KrakenMockAPI(self._kraken_config)

    async def _trigger_ws_message(self, message_data: Dict[str, Any]) -> None:
        """Trigger a WebSocket message in Kraken-specific format."""
        if not self._engine:
            raise RuntimeError("Engine not initialized")

        # Convert to Kraken's expected format and trigger
        ws_client = getattr(self._engine, "_BotEngine__strategy", None)
        if ws_client and hasattr(ws_client, "_GridHODLStrategy__ws_client"):
            await ws_client._GridHODLStrategy__ws_client.on_message(message_data)


# Factory functions for easier test setup
def create_kraken_config(symbol: str) -> KrakenExchangeConfig:
    """Factory to create KrakenExchangeConfig for different symbols."""
    if symbol == "XBTUSD":
        return KrakenExchangeConfig(
            base_currency="XXBT",
            quote_currency="ZUSD",
            pair="XBTUSD",
            ws_symbol="BTC/USD",
        )
    if symbol == "AAPLxUSD":
        return KrakenExchangeConfig(
            base_currency="AAPLx",
            quote_currency="ZUSD",
            pair="AAPLxUSD",
            ws_symbol="AAPLx/USD",
        )
    raise ValueError(f"Unknown symbol: {symbol}")


def create_kraken_bot_config(
    symbol: str,
    strategy: str,
) -> BotConfigDTO:
    """Factory to create BotConfigDTO for Kraken tests."""
    config_map = {
        "XBTUSD": {"base": "BTC", "quote": "USD"},
        "AAPLxUSD": {"base": "AAPLx", "quote": "USD"},
    }

    if symbol not in config_map:
        raise ValueError(f"Unknown symbol: {symbol}")

    currencies = config_map[symbol]

    return BotConfigDTO(
        strategy=strategy,
        exchange="Kraken",
        api_public_key="",
        api_secret_key="",
        name=f"Test Bot {strategy} {currencies['base']}{currencies['quote']}",
        userref=0,
        base_currency=currencies["base"],
        quote_currency=currencies["quote"],
        max_investment=10_000.0,
        amount_per_grid=100.0,
        interval=0.01,
        n_open_buy_orders=5,
        verbosity=0,
    )
