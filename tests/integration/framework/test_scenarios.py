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
