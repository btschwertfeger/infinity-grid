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
from .test_data_models import (
    CDCATestData,
    FillBuyOrderExpectation,
    FillSellOrderExpectation,
    GridHODLTestData,
    GridSellTestData,
    MaxInvestmentExpectation,
    NotEnoughFundsForSellExpectation,
    OrderExpectation,
    RapidPriceDropExpectation,
    SellAfterNotEnoughFundsExpectation,
    ShiftOrdersExpectation,
    SWINGTestData,
    TriggerAllSellOrdersExpectation,
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

    # =============================================================================

    async def run_cdca_scenarios(
        self: Self,
        test_data: CDCATestData,
    ) -> None:
        """
        Run complete cDCA strategy test scenarios.

        Tests the continuous dollar-cost averaging strategy behavior including
        initial order placement, price movements, order filling, and max investment limits.

        Args:
            test_data: Test expectations for cDCA strategy
        """
        # Initialize the algorithm with the initial ticker price
        await self.scenario_prepare_for_trading(test_data.initial_ticker)

        # Ensure the initial buy orders were placed correctly
        await self.scenario_check_initial_buy_orders(
            test_data.check_initial_n_buy_orders,
        )

        # Shift buy orders up and verify the new state
        await self.scenario_shift_buy_orders_up(test_data.trigger_shift_up_buy_orders)

        # Fill a buy order and verify the resulting state
        await self.scenario_fill_buy_order(test_data.trigger_fill_buy_order)

        # Ensure that the correct number of open buy orders are maintained
        await self.scenario_ensure_n_open_buy_orders(
            test_data.trigger_ensure_n_open_buy_orders,
        )

        # Simulate a rapid price drop and verify the resulting state
        await self.scenario_rapid_price_drop(test_data.trigger_rapid_price_drop)

        # Ensure the correct number of open buy orders after the price drop
        await self.scenario_ensure_n_open_buy_orders(
            test_data.trigger_ensure_n_open_buy_orders_after_drop,
        )

        # Check that the max investment condition is handled correctly
        await self.scenario_check_max_investment_reached(
            test_data.check_max_investment_reached,
        )

    async def run_gridhodl_scenarios(self: Self, test_data: GridHODLTestData) -> None:
        """
        Run complete GridHODL strategy test scenarios.

        Tests the Grid HODL strategy behavior including initial order placement,
        buy/sell order filling, rapid price drops, insufficient funds handling,
        and max investment limits.

        Args:
            test_data: Test expectations for GridHODL strategy
        """
        # Initialize and prepare for trading
        await self.scenario_prepare_for_trading(test_data.initial_ticker)

        # Ensure that initial buy orders are placed
        await self.scenario_check_initial_buy_orders(
            test_data.check_initial_n_buy_orders,
        )

        # Shift buy orders up and ensure correct behavior
        await self.scenario_shift_buy_orders_up(test_data.trigger_shift_up_buy_orders)

        # Fill a buy order and ensure correct behavior
        await self.scenario_fill_buy_order(test_data.trigger_fill_buy_order)

        # Ensure that after filling a buy order, the correct number of buy orders are present
        await self.scenario_ensure_n_open_buy_orders(
            test_data.trigger_ensure_n_open_buy_orders,
        )

        # Fill a sell order
        await self.scenario_fill_sell_order(test_data.trigger_fill_sell_order)

        # Check rapid price drop handling
        await self.scenario_rapid_price_drop(test_data.trigger_rapid_price_drop)

        # After rapid price drop, execute the sell orders
        await self.scenario_trigger_all_sell_orders(test_data.trigger_all_sell_orders)

        # Check handling of insufficient funds for selling
        await self.scenario_check_not_enough_funds_for_sell(
            test_data.check_not_enough_funds_for_sell,
        )

        # Sell all after not having enough funds
        await self.scenario_sell_after_not_enough_funds(
            test_data.sell_after_not_enough_funds_for_sell,
        )

        # Check max investment reached
        await self.scenario_check_max_investment_reached(
            test_data.check_max_investment_reached,
        )

    async def run_gridsell_scenarios(
        self: Self,
        test_data: GridSellTestData,
    ) -> None:
        """
        Run complete GridSell strategy test scenarios.

        Tests the Grid Sell strategy behavior including initial order placement,
        buy/sell order filling, rapid price drops, max investment limits,
        and insufficient funds handling (which should cause strategy failure).

        Args:
            test_data: Test expectations for GridSell strategy
        """
        # Initialize and prepare for trading
        await self.scenario_prepare_for_trading(test_data.initial_ticker)

        # Placement of initial buy orders
        await self.scenario_check_initial_buy_orders(
            test_data.check_initial_n_buy_orders,
        )

        # Shifting up buy orders
        await self.scenario_shift_buy_orders_up(test_data.trigger_shift_up_buy_orders)

        # Filling a buy order
        await self.scenario_fill_buy_order(test_data.trigger_fill_buy_order)

        # Ensuring correct number of open buy orders
        await self.scenario_ensure_n_open_buy_orders(
            test_data.trigger_ensure_n_open_buy_orders,
        )

        # Filling a sell order
        await self.scenario_fill_sell_order(test_data.trigger_fill_sell_order)
        # Note: Sell order gets removed from orderbook without creating new buy order
        # unless there are more sell orders. Buy orders shift up if price rises higher.

        # Rapid price drop - filling all buy orders
        await self.scenario_rapid_price_drop(test_data.trigger_rapid_price_drop)

        # Sell all and ensure correct number of open buy orders
        await self.scenario_trigger_all_sell_orders(test_data.trigger_all_sell_orders)

        # Max investment reached
        await self.scenario_check_max_investment_reached(
            test_data.check_max_investment_reached,
        )

        # Retrigger placement of buy orders after max investment
        await self.scenario_ensure_n_open_buy_orders(
            test_data.trigger_ensure_n_open_buy_orders_after_max_investment,
        )

        # Test insufficient funds for sell order - GridSell should fail in this case
        await self.scenario_check_not_enough_funds_for_sell(
            test_data.check_not_enough_funds_for_sell,
            fail=True,  # GridSell should fail in this case
        )

    async def run_swing_scenarios(
        self: Self,
        test_data: SWINGTestData,
    ) -> None:
        """
        Run complete SWING strategy test scenarios.

        Tests the SWING strategy behavior including initial order placement
        (both buy and sell orders), rapid price drops, buy order shifting,
        profit verification, and insufficient funds handling.

        Args:
            test_data: Test expectations for SWING strategy
        """
        # Initialize and prepare for trading
        await self.scenario_prepare_for_trading(test_data.initial_ticker)

        # Ensure that initial buy orders (including sell orders for SWING) are placed
        await self.scenario_check_initial_buy_orders(
            test_data.check_initial_n_buy_orders,
        )

        # Test rapid price drop handling - fills buy orders and creates sell orders
        await self.scenario_rapid_price_drop(test_data.trigger_rapid_price_drop)

        # Ensure correct number of open buy orders after price drop
        await self.scenario_ensure_n_open_buy_orders(
            test_data.trigger_ensure_n_open_buy_orders,
        )

        # Test buy order shifting behavior on price increase and sell order execution
        base_balance_before = float(
            self.manager._mock_api.get_balances()[
                self.manager.exchange_config.base_currency
            ]["balance"],
        )
        quote_balance_before = float(
            self.manager._mock_api.get_balances()[
                self.manager.exchange_config.quote_currency
            ]["balance"],
        )

        await self.scenario_shift_buy_orders_up(test_data.trigger_shift_up_buy_orders)

        # Ensure that profit has been made (sell orders executed)
        assert (
            float(
                self.manager._mock_api.get_balances()[
                    self.manager.exchange_config.base_currency
                ]["balance"],
            )
            < base_balance_before
        )
        assert (
            float(
                self.manager._mock_api.get_balances()[
                    self.manager.exchange_config.quote_currency
                ]["balance"],
            )
            > quote_balance_before
        )

        # Check handling of insufficient funds for selling
        await self.scenario_check_not_enough_funds_for_sell(
            test_data.check_not_enough_funds_for_sell,
        )
    # =============================================================================

    async def scenario_prepare_for_trading(self: Self, initial_ticker: float) -> None:
        """
        Scenario: Prepare the trading engine for trading operations.

        This scenario initializes the engine and triggers the prepare for trading
        sequence with the specified initial ticker price.

        Args:
            initial_ticker: The initial price to use for ticker simulation
        """
        LOG.info(
            "Scenario: Preparing for trading with initial ticker: %s",
            initial_ticker,
        )
        await self.manager.trigger_prepare_for_trading(initial_ticker=initial_ticker)

    async def scenario_check_initial_buy_orders(
        self: Self,
        expectation: OrderExpectation,
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
        expectation: ShiftOrdersExpectation,
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
        expectation: FillBuyOrderExpectation,
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
        expectation: ShiftOrdersExpectation,
    ) -> None:
        """
        Scenario: Ensure correct number of open buy orders.

        This scenario verifies that the strategy maintains the required
        number of open buy orders with correct pricing.

        Args:
            expectation: Expected order configuration
        """
        LOG.info(
            f"Scenario: Ensuring N open buy orders at price: {expectation.new_price}",
        )
        await self.manager.trigger_ensure_n_open_buy_orders(
            new_price=expectation.new_price,
            prices=expectation.prices,
            volumes=expectation.volumes,
            sides=expectation.sides,
        )

    async def scenario_rapid_price_drop(
        self: Self,
        expectation: RapidPriceDropExpectation,
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
        expectation: MaxInvestmentExpectation,
    ) -> None:
        """
        Scenario: Test max investment limit behavior.

        This scenario verifies that the strategy respects maximum investment
        limits and behaves correctly when they are reached.

        Args:
            expectation: Expected max investment behavior
        """
        LOG.info(
            f"Scenario: Checking max investment limit: {expectation.max_investment}",
        )
        await self.manager.check_max_investment_reached(
            current_price=expectation.current_price,
            n_open_sell_orders=expectation.n_open_sell_orders,
            max_investment=expectation.max_investment,
        )

    async def scenario_fill_sell_order(
        self: Self,
        expectation: FillSellOrderExpectation,
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
        expectation: TriggerAllSellOrdersExpectation,
    ) -> None:
        """
        Scenario: Test triggering all sell orders.

        This scenario simulates triggering all sell orders and verifies
        the resulting order configuration.

        Args:
            expectation: Expected all sell orders behavior
        """
        LOG.info(
            f"Scenario: Triggering all sell orders at price: {expectation.new_price}",
        )
        await self.manager.trigger_all_sell_orders(
            new_price=expectation.new_price,
            buy_prices=expectation.buy_prices,
            sell_prices=expectation.sell_prices,
            buy_volumes=expectation.buy_volumes,
            sell_volumes=expectation.sell_volumes,
        )

    async def scenario_check_not_enough_funds_for_sell(
        self: Self,
        expectation: NotEnoughFundsForSellExpectation,
        fail: bool = False,
    ) -> None:
        """
        Scenario: Test insufficient funds for sell order.

        This scenario verifies behavior when there are insufficient funds
        to place a sell order.

        Args:
            expectation: Expected insufficient funds behavior
            fail: Whether the scenario should expect failure (for GridSell)
        """
        LOG.info(
            f"Scenario: Checking insufficient funds for sell at price: {expectation.sell_price}",
        )
        await self.manager.check_not_enough_funds_for_sell(
            sell_price=expectation.sell_price,
            n_orders=expectation.n_orders,
            n_sell_orders=expectation.n_sell_orders,
            assume_base_available=expectation.assume_base_available,
            assume_quote_available=expectation.assume_quote_available,
            fail=fail,
        )

    async def scenario_sell_after_not_enough_funds(
        self: Self,
        expectation: SellAfterNotEnoughFundsExpectation,
    ) -> None:
        """
        Scenario: Test sell behavior after resolving insufficient funds.

        This scenario verifies that missed sell orders are placed once
        sufficient funds become available.

        Args:
            expectation: Expected behavior after resolving insufficient funds
        """
        LOG.info(
            f"Scenario: Selling after insufficient funds resolved at price: {expectation.price}",
        )

        # Simulate ticker update that will place missed orders
        await self.manager._mock_api.simulate_ticker_update(
            callback=self.manager.ws_client.on_message,
            last=expectation.price,
        )

        # Verify the expected order count
        assert self.manager.strategy._orderbook_table.count() == expectation.n_orders

        # Verify sell order prices and volumes
        sell_orders = self.manager.strategy._orderbook_table.get_orders(
            filters={"side": "sell"},
        ).all()

        for order, price, volume in zip(
            sell_orders,
            expectation.sell_prices,
            expectation.sell_volumes,
            strict=True,
        ):
            assert order.price == price
            assert order.volume == volume
