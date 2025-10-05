# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Integration tests for GridHODL strategy using the new scenario-based framework.

This module demonstrates the use of individual test scenarios that can be
tested independently, providing better modularity and test isolation.
"""

import logging
from typing import Callable
from unittest import mock

import pytest

from ..framework.test_data import (
    GRIDHODL_TEST_DATA,
    GRIDHODL_UNFILLED_SURPLUS_TEST_DATA,
    GridHODLTestData,
    GridHODLUnfilledSurplusTestData,
)
from ..framework.test_scenarios import IntegrationTestScenarios

LOG = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_hodl.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("symbol", "test_data"),
    [
        ("XBTUSD", GRIDHODL_TEST_DATA["XBTUSD"]),
        ("AAPLxUSD", GRIDHODL_TEST_DATA["AAPLxUSD"]),
    ],
    ids=("BTCUSD", "AAPLxUSD"),
)
async def test_gridhodl(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    mock_sleep3: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable,
    symbol: str,
    test_data: GridHODLTestData,
) -> None:
    """
    Test the GridHODL strategy scenarios.
    """
    caplog.set_level(logging.INFO)

    test_manager = test_manager_factory("Kraken", symbol, strategy="GridHODL")
    await test_manager.initialize_engine()

    scenarios = IntegrationTestScenarios(test_manager)
    await scenarios.run_gridhodl_scenarios(test_data)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_hodl.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("symbol", "test_data"),
    [
        ("XBTUSD", GRIDHODL_UNFILLED_SURPLUS_TEST_DATA["XBTUSD"]),
        ("AAPLxUSD", GRIDHODL_UNFILLED_SURPLUS_TEST_DATA["AAPLxUSD"]),
    ],
    ids=("BTCUSD", "AAPLxUSD"),
)
async def test_grid_hodl_unfilled_surplus(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.Mock,  # noqa: ARG001
    mock_sleep3: mock.Mock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: pytest.FixtureRequest,
    symbol: str,
    test_data: GridHODLUnfilledSurplusTestData,
) -> None:
    """
    Integration test for the GridHODL strategy using pre-generated websocket
    messages.

    This test checks if the unfilled surplus is handled correctly.

    Unfilled surplus can happen due to partially filled buy orders, that get
    cancelled. When multiple such events happen, the algorithm should sell these
    amounts at the next possible opportunity.

    unfilled surplus: The base currency volume that was partly filled by an buy
    order, before the order was cancelled.
    """
    LOG.info("******* Starting GridHODL unfilled surplus integration test *******")
    caplog.set_level(logging.INFO)

    test_manager = test_manager_factory("Kraken", symbol, strategy="GridHODL")

    await test_manager.initialize_engine()
    scenarios = IntegrationTestScenarios(test_manager)

    # Use scenarios for the common setup parts
    await scenarios.scenario_prepare_for_trading(test_data.initial_ticker)
    await scenarios.scenario_check_initial_buy_orders(
        test_data.check_initial_n_buy_orders,
    )

    # ==========================================================================
    # 2. BUYING PARTLY FILLED and ensure that the unfilled surplus is handled
    LOG.info("******* Check partially filled orders *******")

    # Fill the first buy order partly to accumulate some unfilled surplus.
    test_manager._mock_api.fill_order(
        test_manager.strategy._orderbook_table.get_orders().first().txid,
        test_data.partial_fill.fill_volume,
    )
    assert (
        test_manager.strategy._orderbook_table.count()
        == test_data.partial_fill.n_open_orders
    )

    balances = test_manager._mock_api.get_balances()
    assert (
        float(balances[test_manager.exchange_config.base_currency]["balance"])
        == test_data.partial_fill.expected_base_balance
    )

    assert float(
        balances[test_manager.exchange_config.quote_currency]["balance"],
    ) == pytest.approx(test_data.partial_fill.expected_quote_balance)

    # Cancel the partly filled order
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

    # Place a new buy order to execute cancel logic again.
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

    # Fill the next buy order partly to have enough surplus to trigger a sell
    order = test_manager.strategy._orderbook_table.get_orders(
        filters={"price": test_data.sell_partial_fill.order_price},
    ).all()[0]
    test_manager._mock_api.fill_order(
        order["txid"],
        test_data.partial_fill.fill_volume,
    )
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

    # Ensure that the sell was placed correctly, selling the partially filled
    # surplus
    sell_orders = test_manager.strategy._orderbook_table.get_orders(
        filters={"side": "sell"},
    ).all()
    assert sell_orders[0].price == test_data.sell_partial_fill.expected_sell_price
    assert sell_orders[0].volume == pytest.approx(
        test_data.sell_partial_fill.expected_sell_volume,
    )
