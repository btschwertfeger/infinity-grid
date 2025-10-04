# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Base classes for exchange integration testing.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Protocol, Tuple

from infinity_grid.core.engine import BotEngine
from infinity_grid.models.configuration import (
    BotConfigDTO,
    DBConfigDTO,
    NotificationConfigDTO,
)


class ExchangeTestConfig(Protocol):
    """Protocol for exchange-specific test configuration."""

    base_currency: str
    quote_currency: str
    pair: str
    ws_symbol: str


class MockExchangeAPI(Protocol):
    """Protocol for mocked exchange APIs."""

    def setup_initial_state(self) -> None:
        """Setup initial state for testing."""

    def simulate_ticker_update(self, price: float) -> Dict[str, Any]:
        """Simulate a ticker price update."""

    def simulate_order_fill(self, order_id: str) -> Dict[str, Any]:
        """Simulate an order being filled."""

    def get_open_orders(self) -> List[Dict[str, Any]]:
        """Get currently open orders."""

    def get_balances(self) -> Dict[str, Dict[str, float]]:
        """Get current balances."""


class BaseIntegrationTestManager(ABC):
    """
    Base class for exchange-specific integration test managers.

    This class defines the common interface and shared functionality for
    integration testing across different exchanges, while allowing for
    exchange-specific implementations.
    """

    def __init__(
        self,
        bot_config: BotConfigDTO,
        notification_config: NotificationConfigDTO,
        db_config: DBConfigDTO,
        exchange_config: ExchangeTestConfig,
    ) -> None:
        self.bot_config = bot_config
        self.exchange_config = exchange_config
        self._notification_config = notification_config
        self._db_config = db_config
        self._engine: BotEngine | None = None
        self._mock_api: MockExchangeAPI | None = None

    @abstractmethod
    async def initialize_engine(self) -> None:
        """Initialize the BotEngine with exchange-specific adapters."""
        raise NotImplementedError

    @abstractmethod
    def create_mock_api(self) -> MockExchangeAPI:
        """Create exchange-specific mock API."""
        raise NotImplementedError

    # =========================================================================
    # Common test workflow methods
    # =========================================================================

    async def trigger_prepare_for_trading(self, initial_ticker: float) -> None:
        """
        # 0. PREPARE FOR TRADING

        Initiates the bot initialization phase.
        """
        if not self._engine or not self._mock_api:
            raise RuntimeError(
                "Engine not initialized. Call initialize_engine() first.",
            )

        # Trigger initial ticker update to start trading
        ticker_data = self._mock_api.simulate_ticker_update(initial_ticker)
        await self._trigger_ws_message(ticker_data)

    async def trigger_shift_up_buy_orders(self, new_price: float) -> None:
        """
        # 1. SHIFT UP BUY ORDERS

        Triggers price increase to cause buy order repositioning.
        """
        ticker_data = self._mock_api.simulate_ticker_update(new_price)
        await self._trigger_ws_message(ticker_data)

    async def trigger_fill_buy_order(
        self,
        trigger_price: float,
        _order_price: float,  # Prefix with _ to indicate intentionally unused
    ) -> None:
        """
        # 2. FILL BUY ORDER

        Simulates a buy order being filled at the specified price.
        """
        # First update ticker to trigger price
        ticker_data = self._mock_api.simulate_ticker_update(trigger_price)
        await self._trigger_ws_message(ticker_data)

        # Then simulate order fill
        orders = self._mock_api.get_open_orders()
        buy_order = next(
            (
                o
                for o in orders
                if o["side"] == "buy" and float(o["price"]) >= _order_price
            ),
            None,
        )
        if buy_order:
            fill_data = self._mock_api.simulate_order_fill(buy_order["id"])
            await self._trigger_ws_message(fill_data)

    async def trigger_fill_sell_order(
        self,
        trigger_price: float,
        order_price: float,
    ) -> None:
        """
        # 3. FILL SELL ORDER

        Simulates a sell order being filled at the specified price.
        """
        ticker_data = self._mock_api.simulate_ticker_update(trigger_price)
        await self._trigger_ws_message(ticker_data)

        orders = self._mock_api.get_open_orders()
        sell_order = next(
            (
                o
                for o in orders
                if o["side"] == "sell" and float(o["price"]) <= trigger_price
            ),
            None,
        )
        if sell_order:
            fill_data = self._mock_api.simulate_order_fill(sell_order["id"])
            await self._trigger_ws_message(fill_data)

    # =========================================================================
    # Common validation methods
    # =========================================================================

    def assert_open_orders_count(self, expected_count: int) -> None:
        """Assert the number of open orders."""
        orders = self._mock_api.get_open_orders()
        assert (
            len(orders) == expected_count
        ), f"Expected {expected_count} orders, got {len(orders)}"

    def assert_open_orders_by_side(
        self,
        expected_buy: int,
        expected_sell: int,
    ) -> None:
        """Assert the number of buy and sell orders."""
        orders = self._mock_api.get_open_orders()
        buy_orders = [o for o in orders if o["side"] == "buy"]
        sell_orders = [o for o in orders if o["side"] == "sell"]

        assert (
            len(buy_orders) == expected_buy
        ), f"Expected {expected_buy} buy orders, got {len(buy_orders)}"
        assert (
            len(sell_orders) == expected_sell
        ), f"Expected {expected_sell} sell orders, got {len(sell_orders)}"

    def assert_order_prices_and_volumes(
        self,
        expected_prices: Tuple[float, ...],
        expected_volumes: Tuple[float, ...],
        expected_sides: Tuple[str, ...],
        tolerance: float = 0.1,
    ) -> None:
        """Assert order prices, volumes, and sides match expectations."""
        orders = self._mock_api.get_open_orders()
        orders_sorted = sorted(orders, key=lambda x: float(x["price"]), reverse=True)

        assert len(orders_sorted) == len(expected_prices)

        for i, (order, exp_price, exp_volume, exp_side) in enumerate(
            zip(
                orders_sorted,
                expected_prices,
                expected_volumes,
                expected_sides,
                strict=False,
            ),
        ):
            actual_price = float(order["price"])
            actual_volume = float(order["volume"])
            actual_side = order["side"]

            assert (
                abs(actual_price - exp_price) <= tolerance
            ), f"Order {i}: price {actual_price} != expected {exp_price}"
            assert (
                abs(actual_volume - exp_volume) <= tolerance * exp_volume
            ), f"Order {i}: volume {actual_volume} != expected {exp_volume}"
            assert (
                actual_side == exp_side
            ), f"Order {i}: side {actual_side} != expected {exp_side}"

    def get_balance(self, currency: str) -> float:
        """Get balance for a specific currency."""
        balances = self._mock_api.get_balances()
        return balances.get(currency, {}).get("balance", 0.0)

    # =========================================================================
    # Internal helper methods
    # =========================================================================

    @abstractmethod
    async def _trigger_ws_message(self, message_data: Dict[str, Any]) -> None:
        """Trigger a WebSocket message in exchange-specific format."""
        raise NotImplementedError

    @property
    def engine(self) -> BotEngine:
        """Get the bot engine (must be initialized first)."""
        if not self._engine:
            raise RuntimeError("Engine not initialized")
        return self._engine

    @property
    def mock_api(self) -> MockExchangeAPI:
        """Get the mock API (must be initialized first)."""
        if not self._mock_api:
            raise RuntimeError("Mock API not initialized")
        return self._mock_api
