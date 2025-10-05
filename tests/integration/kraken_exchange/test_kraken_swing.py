# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Integration tests for SWING strategy using the new scenario-based framework.

This module demonstrates the use of individual test scenarios that can be
tested independently, providing better modularity and test isolation.
"""

import logging
from typing import Callable
from unittest import mock

import pytest

from ..framework.test_scenarios import IntegrationTestScenarios
from ..framework.test_data import SWING_TEST_DATA, SWING_UNFILLED_SURPLUS_TEST_DATA
from ..framework.test_data import (
    SWINGTestExpectations,
    SWINGUnfilledSurplusTestExpectations,
)

LOG = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.swing.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("symbol", "test_data"),
    [
        ("XBTUSD", SWING_TEST_DATA["XBTUSD"]),
        ("AAPLxUSD", SWING_TEST_DATA["AAPLxUSD"]),
    ],
    ids=("BTCUSD", "AAPLxUSD"),
)
async def test_swing(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    mock_sleep3: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable,
    symbol: str,
    test_data: SWINGTestExpectations,
) -> None:
    """
    Test the SWING strategy scenarios.
    """
    caplog.set_level(logging.INFO)

    test_manager = test_manager_factory("Kraken", symbol, strategy="SWING")
    await test_manager.initialize_engine()
    scenarios = IntegrationTestScenarios(test_manager)

    # Initialize and prepare for trading
    await scenarios.scenario_prepare_for_trading(test_data.initial_ticker)

    # Ensure that initial buy orders (including sell orders for SWING) are placed
    await scenarios.scenario_check_initial_buy_orders(
        test_data.check_initial_n_buy_orders
    )

    # Test rapid price drop handling - fills buy orders and creates sell orders
    await scenarios.scenario_rapid_price_drop(test_data.trigger_rapid_price_drop)

    # Ensure correct number of open buy orders after price drop
    await scenarios.scenario_ensure_n_open_buy_orders(
        test_data.trigger_ensure_n_open_buy_orders
    )

    # Test buy order shifting behavior on price increase and sell order execution
    base_balance_before = float(
        test_manager._mock_api.get_balances()[
            test_manager.exchange_config.base_currency
        ]["balance"],
    )
    quote_balance_before = float(
        test_manager._mock_api.get_balances()[
            test_manager.exchange_config.quote_currency
        ]["balance"],
    )

    await scenarios.scenario_shift_buy_orders_up(test_data.trigger_shift_up_buy_orders)

    # Ensure that profit has been made (sell orders executed)
    assert (
        float(
            test_manager._mock_api.get_balances()[
                test_manager.exchange_config.base_currency
            ]["balance"]
        )
        < base_balance_before
    )
    assert (
        float(
            test_manager._mock_api.get_balances()[
                test_manager.exchange_config.quote_currency
            ]["balance"]
        )
        > quote_balance_before
    )

    # Check handling of insufficient funds for selling
    await scenarios.scenario_check_not_enough_funds_for_sell(
        test_data.check_not_enough_funds_for_sell
    )


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.swing.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("symbol", "test_data"),
    [
        ("XBTUSD", SWING_UNFILLED_SURPLUS_TEST_DATA["XBTUSD"]),
        ("AAPLxUSD", SWING_UNFILLED_SURPLUS_TEST_DATA["AAPLxUSD"]),
    ],
    ids=("BTCUSD", "AAPLxUSD"),
)
async def test_swing_unfilled_surplus(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    mock_sleep3: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable,
    symbol: str,
    test_data: SWINGUnfilledSurplusTestExpectations,
) -> None:
    """
    Integration test for the SWING strategy unfilled surplus handling.

    This test checks if the unfilled surplus is handled correctly.

    unfilled surplus: The base currency volume that was partly filled by a buy
    order, before the order was cancelled.
    """
    LOG.info("******* Starting SWING unfilled surplus integration test *******")
    caplog.set_level(logging.INFO)

    test_manager = test_manager_factory("Kraken", symbol, strategy="SWING")
    await test_manager.initialize_engine()
    scenarios = IntegrationTestScenarios(test_manager)

    # Initialize and prepare for trading
    await scenarios.scenario_prepare_for_trading(test_data.initial_ticker)

    # ==========================================================================
    # 1. PLACEMENT OF INITIAL N BUY ORDERS
    await scenarios.scenario_check_initial_buy_orders(
        test_data.check_initial_n_buy_orders
    )

    # Check initial balances (SWING creates initial sell order)
    balances = test_manager._mock_api.get_balances()

    assert float(
        balances[test_manager.exchange_config.base_currency]["balance"],
    ) == pytest.approx(test_data.initial_balances.expected_base_balance)
    assert float(
        balances[test_manager.exchange_config.base_currency]["hold_trade"],
    ) == pytest.approx(test_data.initial_balances.expected_base_hold)
    assert float(
        balances[test_manager.exchange_config.quote_currency]["balance"],
    ) == pytest.approx(test_data.initial_balances.expected_quote_balance)
    assert float(
        balances[test_manager.exchange_config.quote_currency]["hold_trade"],
    ) == pytest.approx(test_data.initial_balances.expected_quote_hold)

    # ==========================================================================
    # 2. BUYING PARTLY FILLED and ensure that the unfilled surplus is handled
    # correctly.
    LOG.info("******* Check handling of unfilled surplus *******")
    test_manager._mock_api.fill_order(
        test_manager.strategy._orderbook_table.get_orders().first().txid,
        test_data.partial_fill.fill_volume,
    )
    assert (
        test_manager.strategy._orderbook_table.count()
        == test_data.partial_fill.n_open_orders
    )

    # Check balances after partial fill
    balances = test_manager._mock_api.get_balances()

    assert float(
        balances[test_manager.exchange_config.base_currency]["balance"],
    ) == pytest.approx(test_data.partial_fill_balances.expected_base_balance)
    assert float(
        balances[test_manager.exchange_config.base_currency]["hold_trade"],
    ) == pytest.approx(test_data.partial_fill_balances.expected_base_hold)
    assert float(
        balances[test_manager.exchange_config.quote_currency]["balance"],
    ) == pytest.approx(test_data.partial_fill_balances.expected_quote_balance)
    assert float(
        balances[test_manager.exchange_config.quote_currency]["hold_trade"],
    ) == pytest.approx(test_data.partial_fill_balances.expected_quote_hold)

    # Cancel the partially filled order to trigger unfilled surplus handling
    test_manager.strategy._handle_cancel_order(
        test_manager.strategy._orderbook_table.get_orders().first().txid,
    )

    assert (
        test_manager.strategy._configuration_table.get()["vol_of_unfilled_remaining"]
        == test_data.partial_fill.fill_volume
    )
    assert (
        test_manager.strategy._configuration_table.get()[
            "vol_of_unfilled_remaining_max_price"
        ]
        == test_data.partial_fill.vol_of_unfilled_remaining_max_price
    )

    # ==========================================================================
    # 3. SELLING THE UNFILLED SURPLUS
    #    The sell-check is done only during cancelling orders, as this is the
    #    only time where this amount is touched. So we need to create another
    #    partly filled order.
    LOG.info("******* Check selling the unfilled surplus *******")
    test_manager.strategy.new_buy_order(
        order_price=test_data.sell_partial_fill.order_price,
    )
    assert (
        test_manager.strategy._orderbook_table.count()
        == test_data.sell_partial_fill.n_open_orders
    )
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
        == test_data.sell_partial_fill.n_open_orders
    )

    # Partially fill and cancel the new order to trigger surplus selling
    order = test_manager.strategy._orderbook_table.get_orders(
        filters={"price": test_data.sell_partial_fill.order_price},
    ).all()[0]
    test_manager._mock_api.fill_order(order["txid"], test_data.partial_fill.fill_volume)
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
        == test_data.sell_partial_fill.n_open_orders
    )
    assert (
        test_manager.strategy._configuration_table.get()[
            "vol_of_unfilled_remaining_max_price"
        ]
        == 0.0
    )

    # Verify the sell order for unfilled surplus was created
    sell_orders = test_manager.strategy._orderbook_table.get_orders(
        filters={"side": "sell", "id": 7},
    ).all()
    assert sell_orders[0].price == test_data.sell_partial_fill.expected_sell_price
    assert sell_orders[0].volume == pytest.approx(
        test_data.sell_partial_fill.expected_sell_volume,
    )

    # ==========================================================================
    # 4. MAX INVESTMENT REACHED
    await scenarios.scenario_check_max_investment_reached(
        test_data.check_max_investment_reached
    )
