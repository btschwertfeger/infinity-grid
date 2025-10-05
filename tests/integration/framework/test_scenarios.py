# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Reusable test scenarios for integration testing.

This module contains predefined test scenarios that can be executed
across different exchanges and strategies, ensuring consistent testing
approaches and reducing code duplication.
"""

import logging
from typing import Self
from .base_test_manager import BaseIntegrationTestManager
from .test_data import (
    OrderExpectation,
    FillBuyOrderExpectation,
    ShiftOrdersExpectation,
    RapidPriceDropExpectation,
    MaxInvestmentExpectation,
    FillSellOrderExpectation,
    TriggerAllSellOrdersExpectation,
    NotEnoughFundsForSellExpectation,
    SellAfterNotEnoughFundsExpectation,
)

LOG = logging.getLogger(__name__)


class IntegrationTestScenarios:
    """
    Collection of reusable test scenarios for trading strategies.

    These scenarios are exchange-agnostic and can be used with any
    implementation of BaseIntegrationTestManager. Each scenario tests
    a specific aspect of trading behavior and can be used independently.
    """

    def __init__(self: Self, test_manager: BaseIntegrationTestManager) -> None:
        self.manager = test_manager

    async def scenario_prepare_for_trading(self: Self, initial_ticker: float) -> None:
        """
        Scenario: Prepare the trading engine for trading operations.

        This scenario initializes the engine and triggers the prepare for trading
        sequence with the specified initial ticker price.

        Args:
            initial_ticker: The initial price to use for ticker simulation
        """
        LOG.info(f"Scenario: Preparing for trading with initial ticker: {initial_ticker}")
        await self.manager.trigger_prepare_for_trading(initial_ticker=initial_ticker)

    async def scenario_check_initial_buy_orders(
        self: Self,
        expectation: OrderExpectation
    ) -> None:
        """
        Scenario: Verify initial buy order placement.

        This scenario checks that the correct number of buy orders are placed
        with the expected prices, volumes, and sides.

        Args:
            expectation: Expected order characteristics
        """
        LOG.info("Scenario: Checking initial buy order placement")
        await self.manager.check_initial_n_buy_orders(
            prices=expectation.prices,
            volumes=expectation.volumes,
            sides=expectation.sides,
        )

    async def scenario_shift_buy_orders_up(
        self: Self,
        expectation: ShiftOrdersExpectation
    ) -> None:
        """
        Scenario: Test buy order shifting behavior on price increase.

        This scenario simulates a price increase and verifies that buy orders
        are shifted to appropriate new price levels.

        Args:
            expectation: Expected order shifting behavior
        """
        LOG.info(f"Scenario: Shifting buy orders up to price: {expectation.new_price}")
        await self.manager.trigger_shift_up_buy_orders(
            new_price=expectation.new_price,
            prices=expectation.prices,
            volumes=expectation.volumes,
            sides=expectation.sides,
        )

    async def scenario_fill_buy_order(
        self: Self,
        expectation: FillBuyOrderExpectation
    ) -> None:
        """
        Scenario: Test buy order filling and replacement.

        This scenario simulates filling a buy order and verifies the
        remaining orders are correct and new orders are placed as needed.

        Args:
            expectation: Expected fill behavior and resulting orders
        """
        LOG.info(f"Scenario: Filling buy order at price: {expectation.new_price}")
        await self.manager.trigger_fill_buy_order(
            no_trigger_price=expectation.no_trigger_price,
            new_price=expectation.new_price,
            old_prices=expectation.old_prices,
            old_volumes=expectation.old_volumes,
            old_sides=expectation.old_sides,
            new_prices=expectation.new_prices,
            new_volumes=expectation.new_volumes,
            new_sides=expectation.new_sides,
        )

    async def scenario_ensure_n_open_buy_orders(
        self: Self,
        expectation: ShiftOrdersExpectation
    ) -> None:
        """
        Scenario: Ensure correct number of open buy orders.

        This scenario verifies that the strategy maintains the required
        number of open buy orders with correct pricing.

        Args:
            expectation: Expected order configuration
        """
        LOG.info(f"Scenario: Ensuring N open buy orders at price: {expectation.new_price}")
        await self.manager.trigger_ensure_n_open_buy_orders(
            new_price=expectation.new_price,
            prices=expectation.prices,
            volumes=expectation.volumes,
            sides=expectation.sides,
        )

    async def scenario_rapid_price_drop(
        self: Self,
        expectation: RapidPriceDropExpectation
    ) -> None:
        """
        Scenario: Test behavior during rapid price drops.

        This scenario simulates a rapid price drop that may fill multiple
        orders and verifies the strategy handles it correctly.

        Args:
            expectation: Expected behavior during price drop
        """
        LOG.info(f"Scenario: Rapid price drop to: {expectation.new_price}")
        await self.manager.trigger_rapid_price_drop(
            new_price=expectation.new_price,
            prices=expectation.prices,
            volumes=expectation.volumes,
            sides=expectation.sides,
        )

    async def scenario_check_max_investment_reached(
        self: Self,
        expectation: MaxInvestmentExpectation
    ) -> None:
        """
        Scenario: Test max investment limit behavior.

        This scenario verifies that the strategy respects maximum investment
        limits and behaves correctly when they are reached.

        Args:
            expectation: Expected max investment behavior
        """
        LOG.info(f"Scenario: Checking max investment limit: {expectation.max_investment}")
        await self.manager.check_max_investment_reached(
            current_price=expectation.current_price,
            n_open_sell_orders=expectation.n_open_sell_orders,
            max_investment=expectation.max_investment,
        )

    # =========================================================================
    # GridHOLD-specific scenarios
    # =========================================================================

    async def scenario_fill_sell_order(
        self: Self,
        expectation: FillSellOrderExpectation
    ) -> None:
        """
        Scenario: Test sell order filling behavior.

        This scenario simulates filling a sell order and verifies the
        remaining orders are correct.

        Args:
            expectation: Expected sell order fill behavior
        """
        LOG.info(f"Scenario: Filling sell order at price: {expectation.new_price}")
        await self.manager.trigger_fill_sell_order(
            new_price=expectation.new_price,
            prices=expectation.prices,
            volumes=expectation.volumes,
            sides=expectation.sides,
        )

    async def scenario_trigger_all_sell_orders(
        self: Self,
        expectation: TriggerAllSellOrdersExpectation
    ) -> None:
        """
        Scenario: Test triggering all sell orders.

        This scenario simulates triggering all sell orders and verifies
        the resulting order configuration.

        Args:
            expectation: Expected all sell orders behavior
        """
        LOG.info(f"Scenario: Triggering all sell orders at price: {expectation.new_price}")
        await self.manager.trigger_all_sell_orders(
            new_price=expectation.new_price,
            buy_prices=expectation.buy_prices,
            sell_prices=expectation.sell_prices,
            buy_volumes=expectation.buy_volumes,
            sell_volumes=expectation.sell_volumes,
        )

    async def scenario_check_not_enough_funds_for_sell(
        self: Self,
        expectation: NotEnoughFundsForSellExpectation
    ) -> None:
        """
        Scenario: Test insufficient funds for sell order.

        This scenario verifies behavior when there are insufficient funds
        to place a sell order.

        Args:
            expectation: Expected insufficient funds behavior
        """
        LOG.info(f"Scenario: Checking insufficient funds for sell at price: {expectation.sell_price}")
        await self.manager.check_not_enough_funds_for_sell(
            sell_price=expectation.sell_price,
            n_orders=expectation.n_orders,
            n_sell_orders=expectation.n_sell_orders,
            assume_base_available=expectation.assume_base_available,
            assume_quote_available=expectation.assume_quote_available,
            fail=False,
        )

    async def scenario_sell_after_not_enough_funds(
        self: Self,
        expectation: SellAfterNotEnoughFundsExpectation
    ) -> None:
        """
        Scenario: Test sell behavior after resolving insufficient funds.

        This scenario verifies that missed sell orders are placed once
        sufficient funds become available.

        Args:
            expectation: Expected behavior after resolving insufficient funds
        """
        LOG.info(f"Scenario: Selling after insufficient funds resolved at price: {expectation.price}")

        # Simulate ticker update that will place missed orders
        await self.manager._mock_api.simulate_ticker_update(
            callback=self.manager.ws_client.on_message,
            last=expectation.price,
        )

        # Verify the expected order count
        assert (
            self.manager.strategy._orderbook_table.count() == expectation.n_orders
        )

        # Verify sell order prices and volumes
        sell_orders = self.manager.strategy._orderbook_table.get_orders(
            filters={"side": "sell"}
        ).all()

        for order, price, volume in zip(
            sell_orders,
            expectation.sell_prices,
            expectation.sell_volumes,
            strict=True,
        ):
            assert order.price == price
            assert order.volume == volume
