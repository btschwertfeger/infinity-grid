# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Integration tests for the GridSell strategy on Kraken exchange using the testing framework.

This module demonstrates how to use the new testing framework for strategy testing,
replacing the previous direct test implementation with a more structured approach.
"""

import logging
from collections.abc import Callable
from unittest import mock

import pytest

from ..framework.test_data import (
    GRIDSELL_TEST_DATA,
    GRIDSELL_UNFILLED_SURPLUS_TEST_DATA,
)
from ..framework.test_scenarios import IntegrationTestScenarios
from .kraken_test_manager import KrakenIntegrationTestManager

LOG = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_sell.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("symbol", "test_data"),
    [
        ("XBTUSD", GRIDSELL_TEST_DATA["XBTUSD"]),
        ("AAPLxUSD", GRIDSELL_TEST_DATA["AAPLxUSD"]),
    ],
    ids=("BTCUSD", "AAPLxUSD"),
)
async def test_grid_sell(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    mock_sleep3: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable[[str, str], KrakenIntegrationTestManager],
    symbol: str,
    test_data,
) -> None:
    """
    Integration test for the GridSell strategy using the new testing framework.

    This test simulates the full trading process of the GridSell algorithm, by
    leveraging a mocked Kraken API in order to verify interactions between the
    API, the algorithm and database. The test covers almost all cases that could
    happen during the trading process using structured test scenarios.

    It tests:

    * Handling of ticker updates
    * Handling of execution updates
    * Initialization after the ticker and execution channels are connected
    * Placing of buy orders and shifting them up
    * Execution of buy orders and placement of corresponding sell orders
    * Execution of sell orders
    * Full database interactions using SQLite

    It does not cover the following cases:

    * Interactions related to telegram notifications
    * Initialization of the algorithm
    * Command-line interface / user-like interactions
    """
    LOG.info("******* Starting GridSell integration test using framework *******")
    caplog.set_level(logging.INFO)

    # Initialize test manager and scenarios
    test_manager = test_manager_factory("Kraken", symbol, strategy="GridSell")
    await test_manager.initialize_engine()
    scenarios = IntegrationTestScenarios(test_manager)

    # ==========================================================================
    # INITIALIZATION AND SETUP
    await scenarios.scenario_prepare_for_trading(test_data.initial_ticker)

    # ==========================================================================
    # 1. PLACEMENT OF INITIAL N BUY ORDERS
    await scenarios.scenario_check_initial_buy_orders(
        test_data.check_initial_n_buy_orders
    )

    # ==========================================================================
    # 2. SHIFTING UP BUY ORDERS
    await scenarios.scenario_shift_buy_orders_up(
        test_data.trigger_shift_up_buy_orders
    )

    # ==========================================================================
    # 3. FILLING A BUY ORDER
    await scenarios.scenario_fill_buy_order(
        test_data.trigger_fill_buy_order
    )

    # ==========================================================================
    # 4. ENSURING N OPEN BUY ORDERS
    await scenarios.scenario_ensure_n_open_buy_orders(
        test_data.trigger_ensure_n_open_buy_orders
    )

    # ==========================================================================
    # 5. FILLING A SELL ORDER
    await scenarios.scenario_fill_sell_order(
        test_data.trigger_fill_sell_order
    )

    # ... as we can see, the sell order got removed from the orderbook.
    # ... there is no new corresponding buy order placed - this would only be
    # the case for the case, if there would be more sell orders.
    # As usual, if the price would rise higher, the buy orders would shift up.

    # ==========================================================================
    # 6. RAPID PRICE DROP - FILLING ALL BUY ORDERS
    await scenarios.scenario_rapid_price_drop(
        test_data.trigger_rapid_price_drop
    )

    # ==========================================================================
    # 7. SELL ALL AND ENSURE N OPEN BUY ORDERS
    await scenarios.scenario_trigger_all_sell_orders(
        test_data.trigger_all_sell_orders
    )

    # ==========================================================================
    # 8. MAX INVESTMENT REACHED
    await scenarios.scenario_check_max_investment_reached(
        test_data.check_max_investment_reached
    )

    # After this, we need to retrigger the placement of n buy orders, otherwise
    # the following tests will fail.
    await scenarios.scenario_ensure_n_open_buy_orders(
        test_data.trigger_ensure_n_open_buy_orders_after_max_investment
    )

    # ==========================================================================
    # 9. Test what happens if there are not enough funds to place a sell order
    #    for some reason. The GridSell strategy will fail in this case to trigger
    #    a restart (handled by external process manager)
    await scenarios.scenario_check_not_enough_funds_for_sell(
        test_data.check_not_enough_funds_for_sell,
        fail=True,  # GridSell should fail in this case
    )


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_sell.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("symbol", "expectations"),
    [
        ("XBTUSD", GRIDSELL_UNFILLED_SURPLUS_TEST_DATA["XBTUSD"]),
        ("AAPLxUSD", GRIDSELL_UNFILLED_SURPLUS_TEST_DATA["AAPLxUSD"]),
    ],
    ids=("BTCUSD", "AAPLxUSD"),
)
async def test_kraken_grid_sell_unfilled_surplus(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.Mock,  # noqa: ARG001
    mock_sleep3: mock.Mock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable[[str, str], KrakenIntegrationTestManager],
    symbol: str,
    expectations,
) -> None:
    """
    Integration test for the GridSell strategy using the new testing framework.

    This test checks if the unfilled surplus is handled correctly using
    the structured testing framework.

    unfilled surplus: The base currency volume that was partly filled by a buy
    order, before the order was cancelled.
    """
    LOG.info("******* Starting GridSell unfilled surplus integration test using framework *******")
    caplog.set_level(logging.INFO)

    # Initialize test manager and scenarios
    test_manager = test_manager_factory("Kraken", symbol, strategy="GridSell")
    await test_manager.initialize_engine()
    scenarios = IntegrationTestScenarios(test_manager)

    # ==========================================================================
    # INITIALIZATION AND SETUP
    await scenarios.scenario_prepare_for_trading(expectations.initial_ticker)

    # ==========================================================================
    # 1. PLACEMENT OF INITIAL N BUY ORDERS
    await scenarios.scenario_check_initial_buy_orders(
        expectations.check_initial_n_buy_orders
    )

    # ==========================================================================
    # 2. BUYING PARTLY FILLED and ensure that the unfilled surplus is handled
    LOG.info("******* Check partially filled orders *******")

    test_manager._mock_api.fill_order(
        test_manager.strategy._orderbook_table.get_orders().first().txid,
        expectations.partial_fill.fill_volume,
    )
    assert test_manager.strategy._orderbook_table.count() == expectations.partial_fill.n_open_orders

    balances = test_manager._mock_api.get_balances()
    assert (
        float(balances[test_manager.exchange_config.base_currency]["balance"])
        == expectations.partial_fill.expected_base_balance
    )
    assert float(
        balances[test_manager.exchange_config.quote_currency]["balance"],
    ) == pytest.approx(expectations.partial_fill.expected_quote_balance)

    test_manager.strategy._handle_cancel_order(
        test_manager.strategy._orderbook_table.get_orders().first().txid,
    )

    assert (
        test_manager.strategy._configuration_table.get()["vol_of_unfilled_remaining"]
        == expectations.partial_fill.fill_volume
    )
    assert (
        test_manager.strategy._configuration_table.get()["vol_of_unfilled_remaining_max_price"]
        == expectations.partial_fill.vol_of_unfilled_remaining_max_price
    )

    # ==========================================================================
    # 3. SELLING THE UNFILLED SURPLUS
    #    The sell-check is done only during cancelling orders, as this is the
    #    only time where this amount is touched. So we need to create another
    #    partly filled order.
    LOG.info("******* Check selling the unfilled surplus *******")

    test_manager.strategy.new_buy_order(
        order_price=expectations.sell_partial_fill.order_price,
    )
    assert test_manager.strategy._orderbook_table.count() == expectations.sell_partial_fill.n_open_orders
    assert (
        len(
            [
                o
                for o in test_manager.rest_api.get_open_orders(
                    userref=test_manager.strategy._config.userref,
                )
                if o.status == "open"
            ],
        )
        == expectations.sell_partial_fill.n_open_orders
    )

    order = test_manager.strategy._orderbook_table.get_orders(
        filters={"price": expectations.sell_partial_fill.order_price},
    ).all()[0]
    test_manager._mock_api.fill_order(order["txid"], expectations.partial_fill.fill_volume)
    test_manager.strategy._handle_cancel_order(order["txid"])

    assert (
        len(
            [
                o
                for o in test_manager.rest_api.get_open_orders(
                    userref=test_manager.strategy._config.userref,
                )
                if o.status == "open"
            ],
        )
        == expectations.sell_partial_fill.n_open_orders
    )
    assert (
        test_manager.strategy._configuration_table.get()["vol_of_unfilled_remaining_max_price"]
        == 0.0
    )

    sell_orders = test_manager.strategy._orderbook_table.get_orders(
        filters={"side": "sell"},
    ).all()
    assert (
        sell_orders[0].price
        == expectations.sell_partial_fill.expected_sell_price
    )
    assert sell_orders[0].volume == pytest.approx(
        expectations.sell_partial_fill.expected_sell_volume,
    )
