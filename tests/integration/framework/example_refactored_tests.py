# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Example of refactored integration tests using the new framework.

This demonstrates how the existing Kraken tests can be refactored to use
the exchange-agnostic testing framework, making them more maintainable
and easier to extend to other exchanges.
"""

import logging
from unittest import mock

import pytest

from ..framework.kraken_test_manager import (
    KrakenIntegrationTestManager,
    create_kraken_bot_config,
    create_kraken_config,
)

# Import the framework components
from ..framework.test_data import KRAKEN_TEST_SUITE, StrategyTestExpectations
from ..framework.test_scenarios import (
    IntegrationTestScenarios,
    create_test_parameters_from_suite,
)

LOG = logging.getLogger(__name__)


# Create test parameters from the test suite
TEST_PARAMETERS = create_test_parameters_from_suite(
    KRAKEN_TEST_SUITE,
    strategies=["GridHODL", "GridSell", "SWING", "cDCA"],
)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_hodl.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_sell.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    "symbol,strategy,expectations",
    TEST_PARAMETERS,
    ids=[f"{symbol}-{strategy}" for symbol, strategy, _ in TEST_PARAMETERS],
)
async def test_complete_strategy_workflow(
    symbol: str,
    strategy: str,
    expectations: StrategyTestExpectations,
    db_config,
    notification_config,
) -> None:
    """
    Complete integration test for a strategy using the new framework.

    This single test replaces multiple separate test functions by using
    the scenario-based approach. It's more maintainable and consistent
    across different exchanges and strategies.
    """
    LOG.info("Testing %s strategy on %s", strategy, symbol)

    # Setup test manager
    bot_config = create_kraken_bot_config(symbol, strategy)
    exchange_config = create_kraken_config(symbol)

    test_manager = KrakenIntegrationTestManager(
        bot_config=bot_config,
        notification_config=notification_config,
        db_config=db_config,
        exchange_config=exchange_config,
    )

    # Initialize the test environment
    await test_manager.initialize_engine()

    # Run all test scenarios
    scenarios = IntegrationTestScenarios(test_manager)
    await scenarios.run_complete_strategy_test(expectations)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_hodl.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize("symbol", ["XBTUSD", "AAPLxUSD"])
async def test_initial_setup_only(
    symbol: str,
    db_config,
    notification_config,
) -> None:
    """
    Test only the initial setup scenario for faster feedback during development.

    This demonstrates how individual scenarios can be tested separately
    for debugging or focused testing.
    """
    strategy = "GridHODL"
    expectations = KRAKEN_TEST_SUITE.get_expectations(symbol, strategy)

    # Setup test manager
    bot_config = create_kraken_bot_config(symbol, strategy)
    exchange_config = create_kraken_config(symbol)

    test_manager = KrakenIntegrationTestManager(
        bot_config=bot_config,
        notification_config=notification_config,
        db_config=db_config,
        exchange_config=exchange_config,
    )

    await test_manager.initialize_engine()

    # Run only the initial setup scenario
    scenarios = IntegrationTestScenarios(test_manager)
    await scenarios.scenario_initial_setup(expectations)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
async def test_rapid_price_movements(
    db_config,
    notification_config,
) -> None:
    """
    Focused test for rapid price movement scenarios.

    This shows how to test specific high-risk scenarios that might
    need extra attention or different test data.
    """
    symbol = "XBTUSD"
    strategy = "GridHODL"
    expectations = KRAKEN_TEST_SUITE.get_expectations(symbol, strategy)

    # Setup test manager
    bot_config = create_kraken_bot_config(symbol, strategy)
    exchange_config = create_kraken_config(symbol)

    test_manager = KrakenIntegrationTestManager(
        bot_config=bot_config,
        notification_config=notification_config,
        db_config=db_config,
        exchange_config=exchange_config,
    )

    await test_manager.initialize_engine()

    # Run initial setup first
    scenarios = IntegrationTestScenarios(test_manager)
    await scenarios.scenario_initial_setup(expectations)

    # Then test rapid movements
    await scenarios.scenario_rapid_price_movements(expectations)


# Example of how to add exchange-specific tests while maintaining the framework
@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
async def test_kraken_specific_behavior(
    db_config,
    notification_config,
) -> None:
    """
    Test Kraken-specific behavior that doesn't apply to other exchanges.

    This shows how to add exchange-specific tests while still using
    the common framework infrastructure.
    """
    symbol = "XBTUSD"
    strategy = "GridHODL"
    expectations = KRAKEN_TEST_SUITE.get_expectations(symbol, strategy)

    # Setup using the framework
    bot_config = create_kraken_bot_config(symbol, strategy)
    exchange_config = create_kraken_config(symbol)

    test_manager = KrakenIntegrationTestManager(
        bot_config=bot_config,
        notification_config=notification_config,
        db_config=db_config,
        exchange_config=exchange_config,
    )

    await test_manager.initialize_engine()

    # Run common scenarios
    scenarios = IntegrationTestScenarios(test_manager)
    await scenarios.scenario_initial_setup(expectations)

    # Add Kraken-specific tests
    # For example: test Kraken's specific order validation rules
    orders = test_manager.mock_api.get_open_orders()
    assert all(
        float(order["volume"]) >= 0.0001  # Kraken's minimum BTC order size
        for order in orders
        if order["side"] == "buy"
    )

    # Test Kraken's specific price precision requirements
    assert all(
        len(str(float(order["price"])).split(".")[-1]) <= 1  # Max 1 decimal for XBTUSD
        for order in orders
    )
