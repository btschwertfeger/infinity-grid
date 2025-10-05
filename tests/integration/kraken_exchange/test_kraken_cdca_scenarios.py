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
    ["XBTUSD", "AAPLxUSD"],
    ids=["BTCUSD", "AAPLxUSD"],
)
async def test_scenario_prepare_for_trading(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable,
    symbol: str,
) -> None:
    """Test the prepare for trading scenario."""
    caplog.set_level(logging.INFO)
    expectations = CDCA_TEST_DATA[symbol]

    test_manager = test_manager_factory("Kraken", symbol, strategy="cDCA")
    await test_manager.initialize_engine()
    scenarios = IntegrationTestScenarios(test_manager)

    await scenarios.scenario_prepare_for_trading(expectations.initial_ticker)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    "symbol",
    ["XBTUSD", "AAPLxUSD"],
    ids=["BTCUSD", "AAPLxUSD"],
)
async def test_scenario_check_initial_buy_orders(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable,
    symbol: str,
) -> None:
    """Test the initial buy orders placement scenario."""
    caplog.set_level(logging.INFO)
    expectations = CDCA_TEST_DATA[symbol]

    test_manager = test_manager_factory("Kraken", symbol, strategy="cDCA")
    await test_manager.initialize_engine()
    scenarios = IntegrationTestScenarios(test_manager)

    await scenarios.scenario_prepare_for_trading(expectations.initial_ticker)
    await scenarios.scenario_check_initial_buy_orders(expectations.check_initial_n_buy_orders)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    "symbol",
    ["XBTUSD", "AAPLxUSD"],
    ids=["BTCUSD", "AAPLxUSD"],
)
async def test_scenario_shift_buy_orders_up(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable,
    symbol: str,
) -> None:
    """Test the buy order shifting scenario."""
    caplog.set_level(logging.INFO)
    expectations = CDCA_TEST_DATA[symbol]

    test_manager = test_manager_factory("Kraken", symbol, strategy="cDCA")
    await test_manager.initialize_engine()
    scenarios = IntegrationTestScenarios(test_manager)

    await scenarios.scenario_prepare_for_trading(expectations.initial_ticker)
    await scenarios.scenario_check_initial_buy_orders(expectations.check_initial_n_buy_orders)
    await scenarios.scenario_shift_buy_orders_up(expectations.trigger_shift_up_buy_orders)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    "symbol",
    ["XBTUSD", "AAPLxUSD"],
    ids=["BTCUSD", "AAPLxUSD"],
)
async def test_scenario_fill_buy_order(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable,
    symbol: str,
) -> None:
    """Test the buy order filling scenario."""
    caplog.set_level(logging.INFO)
    expectations = CDCA_TEST_DATA[symbol]

    test_manager = test_manager_factory("Kraken", symbol, strategy="cDCA")
    await test_manager.initialize_engine()
    scenarios = IntegrationTestScenarios(test_manager)

    await scenarios.scenario_prepare_for_trading(expectations.initial_ticker)
    await scenarios.scenario_check_initial_buy_orders(expectations.check_initial_n_buy_orders)
    await scenarios.scenario_shift_buy_orders_up(expectations.trigger_shift_up_buy_orders)
    await scenarios.scenario_fill_buy_order(expectations.trigger_fill_buy_order)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    "symbol",
    ["XBTUSD", "AAPLxUSD"],
    ids=["BTCUSD", "AAPLxUSD"],
)
async def test_scenario_ensure_n_open_buy_orders(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable,
    symbol: str,
) -> None:
    """Test the ensure N open buy orders scenario."""
    caplog.set_level(logging.INFO)
    expectations = CDCA_TEST_DATA[symbol]

    test_manager = test_manager_factory("Kraken", symbol, strategy="cDCA")
    await test_manager.initialize_engine()
    scenarios = IntegrationTestScenarios(test_manager)

    await scenarios.scenario_prepare_for_trading(expectations.initial_ticker)
    await scenarios.scenario_check_initial_buy_orders(expectations.check_initial_n_buy_orders)
    await scenarios.scenario_shift_buy_orders_up(expectations.trigger_shift_up_buy_orders)
    await scenarios.scenario_fill_buy_order(expectations.trigger_fill_buy_order)
    await scenarios.scenario_ensure_n_open_buy_orders(expectations.trigger_ensure_n_open_buy_orders)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    "symbol",
    ["XBTUSD", "AAPLxUSD"],
    ids=["BTCUSD", "AAPLxUSD"],
)
async def test_scenario_rapid_price_drop(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable,
    symbol: str,
) -> None:
    """Test the rapid price drop scenario."""
    caplog.set_level(logging.INFO)
    expectations = CDCA_TEST_DATA[symbol]

    test_manager = test_manager_factory("Kraken", symbol, strategy="cDCA")
    await test_manager.initialize_engine()
    scenarios = IntegrationTestScenarios(test_manager)

    await scenarios.scenario_prepare_for_trading(expectations.initial_ticker)
    await scenarios.scenario_check_initial_buy_orders(expectations.check_initial_n_buy_orders)
    await scenarios.scenario_shift_buy_orders_up(expectations.trigger_shift_up_buy_orders)
    await scenarios.scenario_fill_buy_order(expectations.trigger_fill_buy_order)
    await scenarios.scenario_ensure_n_open_buy_orders(expectations.trigger_ensure_n_open_buy_orders)
    await scenarios.scenario_rapid_price_drop(expectations.trigger_rapid_price_drop)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    "symbol",
    ["XBTUSD", "AAPLxUSD"],
    ids=["BTCUSD", "AAPLxUSD"],
)
async def test_scenario_check_max_investment_reached(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable,
    symbol: str,
) -> None:
    """Test the max investment reached scenario."""
    caplog.set_level(logging.INFO)
    expectations = CDCA_TEST_DATA[symbol]

    test_manager = test_manager_factory("Kraken", symbol, strategy="cDCA")
    await test_manager.initialize_engine()
    scenarios = IntegrationTestScenarios(test_manager)

    # Build up to the max investment scenario
    await scenarios.scenario_prepare_for_trading(expectations.initial_ticker)
    await scenarios.scenario_check_initial_buy_orders(expectations.check_initial_n_buy_orders)
    await scenarios.scenario_shift_buy_orders_up(expectations.trigger_shift_up_buy_orders)
    await scenarios.scenario_fill_buy_order(expectations.trigger_fill_buy_order)
    await scenarios.scenario_ensure_n_open_buy_orders(expectations.trigger_ensure_n_open_buy_orders)
    await scenarios.scenario_rapid_price_drop(expectations.trigger_rapid_price_drop)
    await scenarios.scenario_ensure_n_open_buy_orders(expectations.trigger_ensure_n_open_buy_orders_after_drop)
    await scenarios.scenario_check_max_investment_reached(expectations.check_max_investment_reached)
