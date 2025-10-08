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

from ..framework.test_data_models import (
    BalanceExpectation,
    MaxInvestmentExpectation,
    NotEnoughFundsForSellExpectation,
    OrderExpectation,
    PartialFillExpectation,
    RapidPriceDropExpectation,
    SellPartialFillExpectation,
    ShiftOrdersExpectation,
    SWINGTestData,
    SWINGUnfilledSurplusTestData,
)
from ..framework.test_scenarios import IntegrationTestScenarios

LOG = logging.getLogger(__name__)


SWING_XBTUSD_EXPECTATIONS = SWINGTestData(
    initial_ticker=50_000.0,
    check_initial_n_buy_orders=OrderExpectation(
        prices=(
            49_504.9,
            49_014.7,
            48_529.4,
            48_048.9,
            47_573.1,
            51_005.0,
        ),
        volumes=(
            0.00202,
            0.0020402,
            0.0020606,
            0.00208121,
            0.00210202,
            0.00197044,
        ),
        sides=("buy", "buy", "buy", "buy", "buy", "sell"),
    ),
    trigger_rapid_price_drop=RapidPriceDropExpectation(
        new_price=40_000.0,
        prices=(
            51_005.0,
            49_999.9,
            49_504.8,
            49_014.6,
            48_529.3,
            48_048.8,
        ),
        volumes=(
            0.00197044,
            0.00201005,
            0.00203015,
            0.00205046,
            0.00207096,
            0.00209167,
        ),
        sides=("sell", "sell", "sell", "sell", "sell", "sell"),
    ),
    trigger_ensure_n_open_buy_orders=ShiftOrdersExpectation(
        new_price=40_000.1,
        prices=(
            51_005.0,
            49_999.9,
            49_504.8,
            49_014.6,
            48_529.3,
            48_048.8,
            39_604.0,
            39_211.8,
            38_823.5,
            38_439.1,
            38_058.5,
        ),
        volumes=(
            0.00197044,
            0.00201005,
            0.00203015,
            0.00205046,
            0.00207096,
            0.00209167,
            0.00252499,
            0.00255025,
            0.00257575,
            0.00260151,
            0.00262753,
        ),
        sides=(
            "sell",
            "sell",
            "sell",
            "sell",
            "sell",
            "sell",
            "buy",
            "buy",
            "buy",
            "buy",
            "buy",
        ),
    ),
    trigger_shift_up_buy_orders=ShiftOrdersExpectation(
        new_price=60_000.0,
        prices=(
            59_405.9,
            58_817.7,
            58_235.3,
            57_658.7,
            57_087.8,
        ),
        volumes=(
            0.00168333,
            0.00170016,
            0.00171717,
            0.00173434,
            0.00175168,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    check_not_enough_funds_for_sell=NotEnoughFundsForSellExpectation(
        sell_price=59_000.0,
        n_orders=4,
        n_sell_orders=0,
        assume_base_available=0.0,
        assume_quote_available=1_000.0,
    ),
)

SWING_AAPLXUSD_EXPECTATIONS = SWINGTestData(
    initial_ticker=260.0,
    check_initial_n_buy_orders=OrderExpectation(
        prices=(
            257.42,
            254.87,
            252.34,
            249.84,
            247.36,
            265.22,
        ),
        volumes=(
            0.3884702,
            0.39235688,
            0.39629071,
            0.40025616,
            0.40426908,
            0.37689471,
        ),
        sides=("buy", "buy", "buy", "buy", "buy", "sell"),
    ),
    trigger_rapid_price_drop=RapidPriceDropExpectation(
        new_price=250.0,
        prices=(
            249.84,
            247.36,
            265.22,
            259.99,
            257.41,
            254.86,
        ),
        volumes=(
            0.40025616,
            0.40426908,
            0.37689471,
            0.38447638,
            0.38832996,
            0.39221539,
        ),
        sides=("buy", "buy", "sell", "sell", "sell", "sell"),
    ),
    trigger_ensure_n_open_buy_orders=ShiftOrdersExpectation(
        new_price=250.1,
        prices=(
            249.84,
            247.36,
            265.22,
            259.99,
            257.41,
            254.86,
            244.91,
            242.48,
            240.07,
        ),
        volumes=(
            0.40025616,
            0.40426908,
            0.37689471,
            0.38447638,
            0.38832996,
            0.39221539,
            0.40831325,
            0.41240514,
            0.41654517,
        ),
        sides=(
            "buy",
            "buy",
            "sell",
            "sell",
            "sell",
            "sell",
            "buy",
            "buy",
            "buy",
        ),
    ),
    trigger_shift_up_buy_orders=ShiftOrdersExpectation(
        new_price=255.0,
        prices=(
            249.84,
            247.36,
            265.22,
            259.99,
            257.41,
            244.91,
            242.48,
            240.07,
        ),
        volumes=(
            0.40025616,
            0.40426908,
            0.37689471,
            0.38447638,
            0.38832996,
            0.40831325,
            0.41240514,
            0.41654517,
        ),
        sides=(
            "buy",
            "buy",
            "sell",
            "sell",
            "sell",
            "buy",
            "buy",
            "buy",
        ),
    ),
    check_not_enough_funds_for_sell=NotEnoughFundsForSellExpectation(
        sell_price=257.41,
        n_orders=7,
        n_sell_orders=2,
        assume_base_available=0.0,
        assume_quote_available=1_000.0,
    ),
)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.swing.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("symbol", "test_data"),
    [
        ("XBTUSD", SWING_XBTUSD_EXPECTATIONS),
        ("AAPLxUSD", SWING_AAPLXUSD_EXPECTATIONS),
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
    test_data: SWINGTestData,
) -> None:
    """
    Test the SWING strategy scenarios.
    """
    caplog.set_level(logging.INFO)

    test_manager = test_manager_factory("Kraken", symbol, strategy="SWING")
    await test_manager.initialize_engine()

    scenarios = IntegrationTestScenarios(test_manager)
    await scenarios.run_swing_scenarios(test_data)


SWING_UNFILLED_SURPLUS_XBTUSD_EXPECTATIONS = SWINGUnfilledSurplusTestData(
    initial_ticker=50_000.0,
    check_initial_n_buy_orders=OrderExpectation(
        prices=(
            49_504.9,
            49_014.7,
            48_529.4,
            48_048.9,
            47_573.1,
            51_005.0,
        ),
        volumes=(
            0.00202,
            0.0020402,
            0.0020606,
            0.00208121,
            0.00210202,
            0.00197044,
        ),
        sides=("buy", "buy", "buy", "buy", "buy", "sell"),
    ),
    initial_balances=BalanceExpectation(
        expected_base_balance=99.99802956,  # Adjusted for initial sell order
        expected_base_hold=0.00197044,
        expected_quote_balance=999_500.0011705891,
        expected_quote_hold=499.99882941100003,
    ),
    partial_fill=PartialFillExpectation(
        fill_volume=0.002,
        n_open_orders=6,
        expected_base_balance=100.002,
        expected_quote_balance=999_400.99,
        vol_of_unfilled_remaining_max_price=49_504.9,
    ),
    partial_fill_balances=BalanceExpectation(
        expected_base_balance=100.00002956,  # Adjusted for SWING initial sell order
        expected_base_hold=0.00197044,
        expected_quote_balance=999_400.9913705891,
        expected_quote_hold=400.98902941100005,
    ),
    sell_partial_fill=SellPartialFillExpectation(
        order_price=49_504.9,
        n_open_orders=6,
        expected_sell_price=50_500.0,
        expected_sell_volume=0.00199014,
    ),
    check_max_investment_reached=MaxInvestmentExpectation(
        current_price=50_000.0,
        n_open_sell_orders=2,
        max_investment=0.0,  # Not used in SWING strategy
    ),
)

SWING_UNFILLED_SURPLUS_AAPLXUSD_EXPECTATIONS = SWINGUnfilledSurplusTestData(
    initial_ticker=260.0,
    check_initial_n_buy_orders=OrderExpectation(
        prices=(
            257.42,
            254.87,
            252.34,
            249.84,
            247.36,
            265.22,
        ),
        volumes=(
            0.3884702,
            0.39235688,
            0.39629071,
            0.40025616,
            0.40426908,
            0.37689471,
        ),
        sides=("buy", "buy", "buy", "buy", "buy", "sell"),
    ),
    initial_balances=BalanceExpectation(
        expected_base_balance=99.62310529,  # Adjusted for initial sell order
        expected_base_hold=0.37689471,
        expected_quote_balance=999_499.995,
        expected_quote_hold=499.99990071522,
    ),
    partial_fill=PartialFillExpectation(
        fill_volume=0.3,
        n_open_orders=6,
        expected_base_balance=100.3,
        expected_quote_balance=999_422.77401,
        vol_of_unfilled_remaining_max_price=257.42,
    ),
    partial_fill_balances=BalanceExpectation(
        expected_base_balance=99.92310529,  # Adjusted for SWING initial sell order
        expected_base_hold=0.37689471,
        expected_quote_balance=999_422.769,
        expected_quote_hold=422.7740107152,
    ),
    sell_partial_fill=SellPartialFillExpectation(
        order_price=257.42,
        n_open_orders=6,
        expected_sell_price=262.6,
        expected_sell_volume=0.38065504,
    ),
    check_max_investment_reached=MaxInvestmentExpectation(
        current_price=257.42,
        n_open_sell_orders=2,
        max_investment=0.0,  # Not used in SWING strategy
    ),
)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.swing.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("symbol", "test_data"),
    [
        ("XBTUSD", SWING_UNFILLED_SURPLUS_XBTUSD_EXPECTATIONS),
        ("AAPLxUSD", SWING_UNFILLED_SURPLUS_AAPLXUSD_EXPECTATIONS),
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
    test_data: SWINGUnfilledSurplusTestData,
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
        test_data.check_initial_n_buy_orders,
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
        test_data.check_max_investment_reached,
    )
