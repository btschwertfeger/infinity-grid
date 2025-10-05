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

from ..framework.test_scenarios import IntegrationTestScenarios
from ..framework.test_data import GRIDHODL_TEST_DATA


import logging
from decimal import Decimal
from typing import Callable
from unittest import mock

import pytest

LOG = logging.getLogger(__name__)

@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_hodl.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize("symbol", ["XBTUSD", "AAPLxUSD"])
async def test_gridhodl(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    mock_sleep3: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable,
    symbol: str,
) -> None:
    """
    Test the GridHODL strategy scenarios.
    """
    caplog.set_level(logging.INFO)
    expectations = GRIDHODL_TEST_DATA[symbol]

    test_manager = test_manager_factory("Kraken", symbol, strategy="GridHODL")
    await test_manager.initialize_engine()
    scenarios = IntegrationTestScenarios(test_manager)

    await scenarios.scenario_prepare_for_trading(expectations.initial_ticker)
    await scenarios.scenario_check_initial_buy_orders(
        expectations.check_initial_n_buy_orders
    )
    await scenarios.scenario_shift_buy_orders_up(
        expectations.trigger_shift_up_buy_orders
    )
    await scenarios.scenario_fill_buy_order(expectations.trigger_fill_buy_order)
    await scenarios.scenario_ensure_n_open_buy_orders(
        expectations.trigger_ensure_n_open_buy_orders
    )
    await scenarios.scenario_fill_sell_order(expectations.trigger_fill_sell_order)
    await scenarios.scenario_rapid_price_drop(expectations.trigger_rapid_price_drop)
    await scenarios.scenario_trigger_all_sell_orders(
        expectations.trigger_all_sell_orders
    )
    await scenarios.scenario_check_not_enough_funds_for_sell(
        expectations.check_not_enough_funds_for_sell
    )
    await scenarios.scenario_sell_after_not_enough_funds(
        expectations.sell_after_not_enough_funds_for_sell
    )
    await scenarios.scenario_check_max_investment_reached(
        expectations.check_max_investment_reached
    )

@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_hodl.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("symbol", "expectations"),
    [
        (
            "XBTUSD",
            {
                "initial_ticker": 50_000.0,
                "1_check_initial_n_buy_orders": {
                    "prices": (
                        49_504.9,
                        49_014.7,
                        48_529.4,
                        48_048.9,
                        47_573.1,
                    ),
                    "volumes": (
                        0.00202,
                        0.0020402,
                        0.0020606,
                        0.00208121,
                        0.00210202,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy"),
                },
                "2_partial_fill": {
                    "fill_volume": 0.002,
                    "n_open_orders": 5,
                    "expected_base_balance": Decimal("100.002"),
                    "expected_quote_balance": 999_400.99,
                    "vol_of_unfilled_remaining_max_price": 49_504.9,
                },
                "3_sell_partial_fill": {
                    "order_price": 49_504.9,
                    "n_open_orders": 5,
                    "expected_sell_price": 50_500.0,
                    "expected_sell_volume": 0.00199014,
                },
            },
        ),
        (
            "AAPLxUSD",
            {
                "initial_ticker": 260.0,
                "1_check_initial_n_buy_orders": {
                    "prices": (257.42, 254.87, 252.34, 249.84, 247.36),
                    "volumes": (
                        0.3884702,
                        0.39235688,
                        0.39629071,
                        0.40025616,
                        0.40426908,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy"),
                },
                "2_partial_fill": {
                    "fill_volume": 0.3,
                    "n_open_orders": 5,
                    "expected_base_balance": Decimal("100.3"),
                    "expected_quote_balance": 999422.77401,
                    "vol_of_unfilled_remaining_max_price": 257.42,
                },
                "3_sell_partial_fill": {
                    "order_price": 257.42,
                    "n_open_orders": 5,
                    "expected_sell_price": 262.6,
                    "expected_sell_volume": 0.38065504,
                },
            },
        ),
    ],
    ids=("BTCUSD", "AAPLxUSD"),
)
async def test_kraken_grid_hodl_unfilled_surplus(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.Mock,  # noqa: ARG001
    mock_sleep3: mock.Mock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: pytest.FixtureRequest,
    symbol: str,
    expectations: dict,
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

    tm = test_manager_factory("Kraken", symbol, strategy="GridHODL")
    await tm.initialize_engine()
    await tm.trigger_prepare_for_trading(initial_ticker=expectations["initial_ticker"])

    # ==========================================================================
    # 1. PLACEMENT OF INITIAL N BUY ORDERS
    await tm.check_initial_n_buy_orders(
        prices=expectations["1_check_initial_n_buy_orders"]["prices"],
        volumes=expectations["1_check_initial_n_buy_orders"]["volumes"],
        sides=expectations["1_check_initial_n_buy_orders"]["sides"],
    )

    # ==========================================================================
    # 2. BUYING PARTLY FILLED and ensure that the unfilled surplus is handled
    LOG.info("******* Check partially filled orders *******")
    api = tm.ws_client.__websocket_service

    # Fill the first buy order partly to accumulate some unfilled surplus.
    api.fill_order(
        tm.strategy._orderbook_table.get_orders().first().txid,
        expectations["2_partial_fill"]["fill_volume"],
    )
    assert (
        tm.strategy._orderbook_table.count()
        == expectations["2_partial_fill"]["n_open_orders"]
    )

    balances = api.get_balances()
    assert (
        Decimal(balances[tm.exchange_config.base_currency]["balance"])
        == expectations["2_partial_fill"]["expected_base_balance"]
    )

    assert float(
        balances[tm.exchange_config.quote_currency]["balance"],
    ) == pytest.approx(expectations["2_partial_fill"]["expected_quote_balance"])

    # Cancel the partly filled order
    tm.strategy._handle_cancel_order(
        tm.strategy._orderbook_table.get_orders().first().txid,
    )

    assert (
        tm.strategy._configuration_table.get()["vol_of_unfilled_remaining"]
        == expectations["2_partial_fill"]["fill_volume"]
    )
    assert (
        tm.strategy._configuration_table.get()["vol_of_unfilled_remaining_max_price"]
        == expectations["2_partial_fill"]["vol_of_unfilled_remaining_max_price"]
    )

    # ==========================================================================
    # 3. SELLING THE UNFILLED SURPLUS
    #    The sell-check is done only during cancelling orders, as this is the
    #    only time where this amount is touched. So we need to create another
    #    partly filled order.
    LOG.info("******* Check selling the unfilled surplus *******")

    # Place a new buy order to execute cancel logic again.
    tm.strategy.new_buy_order(
        order_price=expectations["3_sell_partial_fill"]["order_price"],
    )
    assert (
        tm.strategy._orderbook_table.count()
        == expectations["3_sell_partial_fill"]["n_open_orders"]
    )
    assert (
        len(
            [
                o
                for o in tm.rest_api.get_open_orders(
                    userref=tm.strategy._config.userref,
                )
                if o.status == "open"
            ],
        )
        == expectations["3_sell_partial_fill"]["n_open_orders"]
    )

    # Fill the next buy order partly to have enough surplus to trigger a sell
    order = tm.strategy._orderbook_table.get_orders(
        filters={"price": expectations["3_sell_partial_fill"]["order_price"]},
    ).all()[0]
    api.fill_order(order["txid"], expectations["2_partial_fill"]["fill_volume"])
    tm.strategy._handle_cancel_order(order["txid"])

    assert (
        len(
            [
                o
                for o in tm.rest_api.get_open_orders(
                    userref=tm.strategy._config.userref,
                )
                if o.status == "open"
            ],
        )
        == expectations["3_sell_partial_fill"]["n_open_orders"]
    )
    assert (
        tm.strategy._configuration_table.get()["vol_of_unfilled_remaining_max_price"]
        == 0.0
    )

    # Ensure that the sell was placed correctly, selling the partially filled
    # surplus
    sell_orders = tm.strategy._orderbook_table.get_orders(
        filters={"side": "sell"},
    ).all()
    assert (
        sell_orders[0].price
        == expectations["3_sell_partial_fill"]["expected_sell_price"]
    )
    assert sell_orders[0].volume == pytest.approx(
        expectations["3_sell_partial_fill"]["expected_sell_volume"],
    )
