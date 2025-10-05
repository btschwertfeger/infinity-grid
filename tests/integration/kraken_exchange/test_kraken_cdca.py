# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Integration tests for cDCA strategy using the new scenario-based framework.

This module demonstrates the use of individual test scenarios that can be
tested independently, providing better modularity and test isolation.
"""

import logging
from typing import Callable
from unittest import mock

import pytest

from ..framework.test_data_models import (
    CDCATestData,
    FillBuyOrderExpectation,
    MaxInvestmentExpectation,
    OrderExpectation,
    RapidPriceDropExpectation,
    ShiftOrdersExpectation,
)
from ..framework.test_scenarios import IntegrationTestScenarios

CDCA_XBTUSD_EXPECTATIONS = CDCATestData(
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
        ),
        new_volumes=(
            0.00170016,
            0.00171717,
            0.00173434,
            0.00175168,
        ),
        new_sides=("buy", "buy", "buy", "buy"),
    ),
    trigger_ensure_n_open_buy_orders=ShiftOrdersExpectation(
        new_price=59_100.0,
        prices=(58_817.7, 58_235.3, 57_658.7, 57_087.8, 56_522.5),
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
        prices=(),
        volumes=(),
        sides=(),
    ),
    trigger_ensure_n_open_buy_orders_after_drop=ShiftOrdersExpectation(
        new_price=50_100.0,
        prices=(
            49_603.9,
            49_112.7,
            48_626.4,
            48_144.9,
            47_668.2,
        ),
        volumes=(
            0.00201597,
            0.00203613,
            0.00205649,
            0.00207706,
            0.00209783,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    check_max_investment_reached=MaxInvestmentExpectation(
        current_price=50_000.0,
        n_open_sell_orders=0,
        max_investment=50.0,
    ),
)

CDCA_AAPLXUSD_EXPECTATIONS = CDCATestData(
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
        new_prices=(274.47, 271.75, 269.05, 266.38),
        new_volumes=(
            0.36433854,
            0.36798528,
            0.37167812,
            0.37540355,
        ),
        new_sides=("buy", "buy", "buy", "buy"),
    ),
    trigger_ensure_n_open_buy_orders=ShiftOrdersExpectation(
        new_price=277.1,
        prices=(274.47, 271.75, 269.05, 266.38, 263.74),
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
        prices=(),
        volumes=(),
        sides=(),
    ),
    trigger_ensure_n_open_buy_orders_after_drop=ShiftOrdersExpectation(
        new_price=260.0,
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
    check_max_investment_reached=MaxInvestmentExpectation(
        current_price=260.0,
        n_open_sell_orders=0,
        max_investment=50.0,
    ),
)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("symbol", "test_data"),
    [
        ("XBTUSD", CDCA_XBTUSD_EXPECTATIONS),
        ("AAPLxUSD", CDCA_AAPLXUSD_EXPECTATIONS),
    ],
    ids=["XBTUSD", "AAPLxUSD"],
)
async def test_cdca(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable,
    symbol: str,
    test_data: CDCATestData,
) -> None:
    """
    Test the cDCA strategy on Kraken exchange using predefined scenarios.
    """
    caplog.set_level(logging.INFO)

    test_manager = test_manager_factory("Kraken", symbol, strategy="cDCA")
    await test_manager.initialize_engine()

    scenarios = IntegrationTestScenarios(test_manager)
    await scenarios.run_cdca_scenarios(test_data)
