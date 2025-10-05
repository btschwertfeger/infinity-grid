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

from ..framework.test_scenarios import IntegrationTestScenarios
from ..framework.test_data import CDCA_TEST_DATA


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    "symbol",
    ["XBTUSD", "AAPLxUSD"]
)
async def test_cdca(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable,
    symbol: str,
) -> None:
    """
    Test the cDCA strategy on Kraken exchange using predefined scenarios.
    """
    caplog.set_level(logging.INFO)
    expectations = CDCA_TEST_DATA[symbol]

    test_manager = test_manager_factory("Kraken", symbol, strategy="cDCA")
    await test_manager.initialize_engine()
    scenarios = IntegrationTestScenarios(test_manager)

    # Initialize the algorithm with the initial ticker price
    await scenarios.scenario_prepare_for_trading(expectations.initial_ticker)
    # Ensure the initial n open buy orders were placed correctly
    await scenarios.scenario_check_initial_buy_orders(
        expectations.check_initial_n_buy_orders
    )
    # Shift buy orders up and verify the new state
    await scenarios.scenario_shift_buy_orders_up(
        expectations.trigger_shift_up_buy_orders
    )
    # Fill a buy order and verify the resulting state
    await scenarios.scenario_fill_buy_order(expectations.trigger_fill_buy_order)
    # Ensure that the correct number of open buy orders are maintained
    await scenarios.scenario_ensure_n_open_buy_orders(
        expectations.trigger_ensure_n_open_buy_orders
    )
    # Simulate a rapid price drop and verify the resulting state
    await scenarios.scenario_rapid_price_drop(expectations.trigger_rapid_price_drop)
    # Again, ensure the correct number of open buy orders after the price drop
    await scenarios.scenario_ensure_n_open_buy_orders(
        expectations.trigger_ensure_n_open_buy_orders_after_drop
    )
    # Finally, check that the max investment condition is handled correctly
    await scenarios.scenario_check_max_investment_reached(
        expectations.check_max_investment_reached
    )
