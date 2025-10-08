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

from ..framework.test_data_models import (
    FillBuyOrderExpectation,
    FillSellOrderExpectation,
    GridHODLTestData,
    GridHODLUnfilledSurplusTestData,
    MaxInvestmentExpectation,
    NotEnoughFundsForSellExpectation,
    OrderExpectation,
    PartialFillExpectation,
    RapidPriceDropExpectation,
    SellAfterNotEnoughFundsExpectation,
    SellPartialFillExpectation,
    ShiftOrdersExpectation,
    TriggerAllSellOrdersExpectation,
)
from ..framework.test_scenarios import IntegrationTestScenarios

LOG = logging.getLogger(__name__)


GRIDHODL_XBTUSD_EXPECTATIONS = GridHODLTestData(
    initial_ticker=50_000.0,
    check_initial_n_buy_orders=OrderExpectation(
        prices=(
            49_504.9,
            49_014.7,
            48_529.4,
            48_048.9,
            47_573.1,
        ),
        volumes=(
            0.00202,
            0.0020402,
            0.0020606,
            0.00208121,
            0.00210202,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
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
    trigger_fill_buy_order=FillBuyOrderExpectation(
        no_trigger_price=59_990.0,
        new_price=59_000.0,
        old_prices=(
            59_405.9,
            58_817.7,
            58_235.3,
            57_658.7,
            57_087.8,
        ),
        old_volumes=(
            0.00168333,
            0.00170016,
            0.00171717,
            0.00173434,
            0.00175168,
        ),
        old_sides=("buy", "buy", "buy", "buy", "buy"),
        new_prices=(
            58_817.7,
            58_235.3,
            57_658.7,
            57_087.8,
            59_999.9,
        ),
        new_volumes=(
            0.00170016,
            0.00171717,
            0.00173434,
            0.00175168,
            0.00167504,
        ),
        new_sides=("buy", "buy", "buy", "buy", "sell"),
    ),
    trigger_ensure_n_open_buy_orders=ShiftOrdersExpectation(
        new_price=59_100.0,
        prices=(
            58_817.7,
            58_235.3,
            57_658.7,
            57_087.8,
            59_999.9,
            56_522.5,
        ),
        volumes=(
            0.00170016,
            0.00171717,
            0.00173434,
            0.00175168,
            0.00167504,
            0.0017692,
        ),
        sides=("buy", "buy", "buy", "buy", "sell", "buy"),
    ),
    trigger_fill_sell_order=FillSellOrderExpectation(
        new_price=60_000.0,
        prices=(
            58_817.7,
            58_235.3,
            57_658.7,
            57_087.8,
            56_522.5,
        ),
        volumes=(
            0.00170016,
            0.00171717,
            0.00173434,
            0.00175168,
            0.0017692,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    trigger_rapid_price_drop=RapidPriceDropExpectation(
        new_price=50_000.0,
        prices=(
            59_405.8,
            58_817.6,
            58_235.2,
            57_658.6,
            57_087.7,
        ),
        volumes=(
            0.00169179,
            0.00170871,
            0.0017258,
            0.00174306,
            0.00176049,
        ),
        sides=("sell", "sell", "sell", "sell", "sell"),
    ),
    trigger_all_sell_orders=TriggerAllSellOrdersExpectation(
        new_price=59_100.0,
        buy_prices=(
            58_514.8,
            57_935.4,
            57_361.7,
            56_793.7,
            56_231.3,
        ),
        sell_prices=(59_405.8,),
        buy_volumes=(
            0.00170896,
            0.00172606,
            0.00174332,
            0.00176075,
            0.00177836,
        ),
        sell_volumes=(0.00169179,),
    ),
    check_not_enough_funds_for_sell=NotEnoughFundsForSellExpectation(
        sell_price=58_500.0,
        n_orders=5,
        n_sell_orders=1,
        assume_base_available=0.0,
        assume_quote_available=1000.0,
    ),
    sell_after_not_enough_funds_for_sell=SellAfterNotEnoughFundsExpectation(
        price=58_500.0,
        n_orders=7,
        sell_prices=(59_405.8, 59_099.9),
        sell_volumes=(0.00169179, 0.00170055),
    ),
    check_max_investment_reached=MaxInvestmentExpectation(
        current_price=50_000.0,
        n_open_sell_orders=2,
        max_investment=202.0,
    ),
)

GRIDHODL_AAPLXUSD_EXPECTATIONS = GridHODLTestData(
    initial_ticker=260.0,
    check_initial_n_buy_orders=OrderExpectation(
        prices=(257.42, 254.87, 252.34, 249.84, 247.36),
        volumes=(
            0.3884702,
            0.39235688,
            0.39629071,
            0.40025616,
            0.40426908,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    trigger_shift_up_buy_orders=ShiftOrdersExpectation(
        new_price=280.0,
        prices=(277.22, 274.47, 271.75, 269.05, 266.38),
        volumes=(
            0.36072433,
            0.36433854,
            0.36798528,
            0.37167812,
            0.37540355,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    trigger_fill_buy_order=FillBuyOrderExpectation(
        no_trigger_price=279.0,
        new_price=277.0,
        old_prices=(277.22, 274.47, 271.75, 269.05, 266.38),
        old_volumes=(
            0.36072433,
            0.36433854,
            0.36798528,
            0.37167812,
            0.37540355,
        ),
        old_sides=("buy", "buy", "buy", "buy", "buy"),
        new_prices=(274.47, 271.75, 269.05, 266.38, 279.99),
        new_volumes=(
            0.36433854,
            0.36798528,
            0.37167812,
            0.37540355,
            0.3570128,
        ),
        new_sides=("buy", "buy", "buy", "buy", "sell"),
    ),
    trigger_ensure_n_open_buy_orders=ShiftOrdersExpectation(
        new_price=277.1,
        prices=(
            274.47,
            271.75,
            269.05,
            266.38,
            279.99,
            263.74,
        ),
        volumes=(
            0.36433854,
            0.36798528,
            0.37167812,
            0.37540355,
            0.3570128,
            0.37916129,
        ),
        sides=("buy", "buy", "buy", "buy", "sell", "buy"),
    ),
    trigger_fill_sell_order=FillSellOrderExpectation(
        new_price=280.0,
        prices=(
            274.47,
            271.75,
            269.05,
            266.38,
            263.74,
        ),
        volumes=(
            0.36433854,
            0.36798528,
            0.37167812,
            0.37540355,
            0.37916129,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    trigger_rapid_price_drop=RapidPriceDropExpectation(
        new_price=260.0,
        prices=(277.21, 274.46, 271.74, 269.04, 266.37),
        volumes=(
            0.3605931,
            0.36420613,
            0.36785168,
            0.37154332,
            0.37526754,
        ),
        sides=("sell", "sell", "sell", "sell", "sell"),
    ),
    trigger_all_sell_orders=TriggerAllSellOrdersExpectation(
        new_price=275.0,
        buy_prices=(
            272.27,
            269.57,
            266.9,
            264.25,
            261.63,
        ),
        sell_prices=(277.21,),
        buy_volumes=(
            0.36728247,
            0.37096116,
            0.37467216,
            0.37842951,
            0.38221916,
        ),
        sell_volumes=(0.3605931,),
    ),
    check_not_enough_funds_for_sell=NotEnoughFundsForSellExpectation(
        sell_price=272.0,
        n_orders=5,
        n_sell_orders=1,
        assume_base_available=0.0,
        assume_quote_available=1000.0,
    ),
    sell_after_not_enough_funds_for_sell=SellAfterNotEnoughFundsExpectation(
        price=272.0,
        n_orders=7,
        sell_prices=(277.21, 274.99),
        sell_volumes=(0.3605931, 0.36350418),
    ),
    check_max_investment_reached=MaxInvestmentExpectation(
        current_price=270.0,
        n_open_sell_orders=2,
        max_investment=202.0,
    ),
)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_hodl.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("symbol", "test_data"),
    [
        ("XBTUSD", GRIDHODL_XBTUSD_EXPECTATIONS),
        ("AAPLxUSD", GRIDHODL_AAPLXUSD_EXPECTATIONS),
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


GRIDHODL_UNFILLED_SURPLUS_XBTUSD_EXPECTATIONS = GridHODLUnfilledSurplusTestData(
    initial_ticker=50_000.0,
    check_initial_n_buy_orders=OrderExpectation(
        prices=(
            49_504.9,
            49_014.7,
            48_529.4,
            48_048.9,
            47_573.1,
        ),
        volumes=(
            0.00202,
            0.0020402,
            0.0020606,
            0.00208121,
            0.00210202,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    partial_fill=PartialFillExpectation(
        fill_volume=0.002,
        n_open_orders=5,
        expected_base_balance=100.002,
        expected_quote_balance=999_400.99,
        vol_of_unfilled_remaining_max_price=49_504.9,
    ),
    sell_partial_fill=SellPartialFillExpectation(
        order_price=49_504.9,
        n_open_orders=5,
        expected_sell_price=50_500.0,
        expected_sell_volume=0.00199014,
    ),
)

GRIDHODL_UNFILLED_SURPLUS_AAPLXUSD_EXPECTATIONS = GridHODLUnfilledSurplusTestData(
    initial_ticker=260.0,
    check_initial_n_buy_orders=OrderExpectation(
        prices=(257.42, 254.87, 252.34, 249.84, 247.36),
        volumes=(
            0.3884702,
            0.39235688,
            0.39629071,
            0.40025616,
            0.40426908,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    partial_fill=PartialFillExpectation(
        fill_volume=0.3,
        n_open_orders=5,
        expected_base_balance=100.3,
        expected_quote_balance=999422.77401,
        vol_of_unfilled_remaining_max_price=257.42,
    ),
    sell_partial_fill=SellPartialFillExpectation(
        order_price=257.42,
        n_open_orders=5,
        expected_sell_price=262.6,
        expected_sell_volume=0.38065504,
    ),
)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_hodl.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("symbol", "test_data"),
    [
        ("XBTUSD", GRIDHODL_UNFILLED_SURPLUS_XBTUSD_EXPECTATIONS),
        ("AAPLxUSD", GRIDHODL_UNFILLED_SURPLUS_AAPLXUSD_EXPECTATIONS),
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
