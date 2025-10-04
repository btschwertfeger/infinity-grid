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
from typing import List, Tuple

from .base_test_manager import BaseIntegrationTestManager
from .test_data import StrategyTestExpectations

LOG = logging.getLogger(__name__)


class IntegrationTestScenarios:
    """
    Collection of reusable test scenarios for trading strategies.

    These scenarios are exchange-agnostic and can be used with any
    implementation of BaseIntegrationTestManager.
    """

    def __init__(self, test_manager: BaseIntegrationTestManager) -> None:
        self.manager = test_manager

    async def scenario_initial_setup(
        self,
        expectations: StrategyTestExpectations,
    ) -> None:
        """
        Scenario: Initial bot setup and order placement.

        Tests:
        - Bot initialization
        - Initial order placement based on current price
        - Correct number of orders placed
        - Order prices and volumes match expectations
        """
        LOG.info("=== Running Scenario: Initial Setup ===")

        # Initialize and start trading
        await self.manager.trigger_prepare_for_trading(expectations.initial_ticker)

        # Validate initial orders
        self.manager.assert_order_prices_and_volumes(
            expected_prices=expectations.initial_orders.prices,
            expected_volumes=expectations.initial_orders.volumes,
            expected_sides=expectations.initial_orders.sides,
        )

        LOG.info("✓ Initial setup completed successfully")

    async def scenario_price_increase_order_shift(
        self,
        expectations: StrategyTestExpectations,
    ) -> None:
        """
        Scenario: Price increase causing buy order repositioning.

        Tests:
        - Response to significant price increases
        - Buy orders are shifted up to new price levels
        - Order volumes adjust for new price levels
        - No orders are triggered during the shift
        """
        LOG.info("=== Running Scenario: Price Increase Order Shift ===")

        shift_expectation = expectations.shift_up_orders

        # Trigger price increase
        await self.manager.trigger_shift_up_buy_orders(shift_expectation.trigger_price)

        # Validate repositioned orders
        self.manager.assert_order_prices_and_volumes(
            expected_prices=shift_expectation.expected_orders.prices,
            expected_volumes=shift_expectation.expected_orders.volumes,
            expected_sides=shift_expectation.expected_orders.sides,
        )

        LOG.info("✓ Price increase order shift completed successfully")

    async def scenario_buy_order_fill(
        self,
        expectations: StrategyTestExpectations,
    ) -> None:
        """
        Scenario: Buy order gets filled.

        Tests:
        - Buy order execution when price crosses order level
        - Sell order placement after buy fill (strategy-dependent)
        - Remaining buy orders stay in place
        - New buy order placement to maintain grid
        """
        LOG.info("=== Running Scenario: Buy Order Fill ===")

        fill_expectation = expectations.fill_buy_order

        # Test that no trigger occurs at no_trigger_price
        if fill_expectation.no_trigger_price:
            await self.manager.trigger_shift_up_buy_orders(
                fill_expectation.no_trigger_price,
            )
            # Verify orders haven't changed significantly

        # Trigger buy order fill
        await self.manager.trigger_fill_buy_order(
            trigger_price=fill_expectation.trigger_price,
            _order_price=fill_expectation.expected_orders.prices[
                0
            ],  # Highest price order
        )

        # Validate post-fill state
        self.manager.assert_order_prices_and_volumes(
            expected_prices=fill_expectation.expected_orders.prices,
            expected_volumes=fill_expectation.expected_orders.volumes,
            expected_sides=fill_expectation.expected_orders.sides,
        )

        LOG.info("✓ Buy order fill completed successfully")

    async def scenario_sell_order_fill(
        self,
        expectations: StrategyTestExpectations,
    ) -> None:
        """
        Scenario: Sell order gets filled (if strategy supports it).

        Tests:
        - Sell order execution when price rises to sell level
        - Profit realization
        - Grid rebalancing after sell
        - Continued buy order placement
        """
        if not expectations.fill_sell_order:
            LOG.info(
                "=== Skipping Scenario: Sell Order Fill (not supported by strategy) ===",
            )
            return

        LOG.info("=== Running Scenario: Sell Order Fill ===")

        sell_expectation = expectations.fill_sell_order

        # Trigger sell order fill
        await self.manager.trigger_fill_sell_order(
            trigger_price=sell_expectation.trigger_price,
            order_price=sell_expectation.expected_orders.prices[0],
        )

        # Validate post-sell state
        self.manager.assert_order_prices_and_volumes(
            expected_prices=sell_expectation.expected_orders.prices,
            expected_volumes=sell_expectation.expected_orders.volumes,
            expected_sides=sell_expectation.expected_orders.sides,
        )

        LOG.info("✓ Sell order fill completed successfully")

    async def scenario_rapid_price_movements(
        self,
        expectations: StrategyTestExpectations,
    ) -> None:
        """
        Scenario: Rapid price movements in both directions.

        Tests:
        - Strategy response to sudden price drops
        - Strategy response to sudden price spikes
        - Order management during volatility
        - System stability under stress
        """
        LOG.info("=== Running Scenario: Rapid Price Movements ===")

        if expectations.rapid_price_drop:
            LOG.info("Testing rapid price drop...")
            drop_expectation = expectations.rapid_price_drop
            await self.manager.trigger_shift_up_buy_orders(
                drop_expectation.trigger_price,
            )

            self.manager.assert_order_prices_and_volumes(
                expected_prices=drop_expectation.expected_orders.prices,
                expected_volumes=drop_expectation.expected_orders.volumes,
                expected_sides=drop_expectation.expected_orders.sides,
            )

        if expectations.rapid_price_rise:
            LOG.info("Testing rapid price rise...")
            rise_expectation = expectations.rapid_price_rise
            await self.manager.trigger_shift_up_buy_orders(
                rise_expectation.trigger_price,
            )

            self.manager.assert_order_prices_and_volumes(
                expected_prices=rise_expectation.expected_orders.prices,
                expected_volumes=rise_expectation.expected_orders.volumes,
                expected_sides=rise_expectation.expected_orders.sides,
            )

        LOG.info("✓ Rapid price movements completed successfully")

    async def scenario_max_investment_limit(
        self,
        expectations: StrategyTestExpectations,
    ) -> None:
        """
        Scenario: Maximum investment limit reached.

        Tests:
        - Bot stops placing new buy orders when limit reached
        - Existing orders remain active
        - Sell orders continue to function
        - System doesn't exceed configured limits
        """
        if not expectations.max_investment_scenario:
            LOG.info("=== Skipping Scenario: Max Investment Limit (not configured) ===")
            return

        LOG.info("=== Running Scenario: Max Investment Limit ===")

        max_invest = expectations.max_investment_scenario

        # Force price down to trigger max investment
        await self.manager.trigger_shift_up_buy_orders(max_invest["current_price"])

        # Verify investment limits are respected
        total_investment = self._calculate_total_investment()
        assert (
            total_investment <= max_invest["max_investment"]
        ), f"Investment {total_investment} exceeds limit {max_invest['max_investment']}"

        # Verify correct number of sell orders
        self.manager.assert_open_orders_by_side(
            expected_buy=0,  # Should stop placing buy orders
            expected_sell=int(max_invest["n_open_sell_orders"]),
        )

        LOG.info("✓ Max investment limit scenario completed successfully")

    def _calculate_total_investment(self) -> float:
        """Calculate total investment from open orders."""
        orders = self.manager.mock_api.get_open_orders()
        total = sum(
            float(order["price"]) * float(order["volume"])
            for order in orders
            if order["side"] == "buy"
        )
        return total

    async def run_complete_strategy_test(
        self,
        expectations: StrategyTestExpectations,
    ) -> None:
        """
        Run a complete test suite for a strategy.

        This executes all applicable scenarios in the correct order,
        providing comprehensive validation of strategy behavior.
        """
        LOG.info("=== Starting Complete Strategy Test ===")

        # Core scenarios (always run)
        await self.scenario_initial_setup(expectations)
        await self.scenario_price_increase_order_shift(expectations)
        await self.scenario_buy_order_fill(expectations)

        # Optional scenarios (strategy-dependent)
        await self.scenario_sell_order_fill(expectations)
        await self.scenario_rapid_price_movements(expectations)
        await self.scenario_max_investment_limit(expectations)

        LOG.info("=== Complete Strategy Test Finished Successfully ===")


def create_test_parameters_from_suite(
    test_suite,
    strategies: List[str],
) -> List[Tuple[str, str, StrategyTestExpectations]]:
    """
    Create pytest parameters from a test suite configuration.

    This helper function generates the parameter combinations needed
    for pytest.mark.parametrize, making it easy to run the same
    test scenarios across multiple symbols and strategies.

    Args:
        test_suite: ExchangeTestSuite configuration
        strategies: List of strategy names to test

    Returns:
        List of (symbol, strategy, expectations) tuples for parameterization
    """
    parameters = []

    for pair in test_suite.trading_pairs:
        symbol = pair.symbol
        if symbol not in test_suite.strategy_expectations:
            continue

        for strategy in strategies:
            if strategy in test_suite.strategy_expectations[symbol]:
                expectations = test_suite.get_expectations(symbol, strategy)
                parameters.append((symbol, strategy, expectations))

    return parameters
