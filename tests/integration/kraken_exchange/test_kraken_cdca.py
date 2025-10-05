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

from ..framework.test_data import CDCA_TEST_DATA, CDCATestData
from ..framework.test_scenarios import IntegrationTestScenarios


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("symbol", "test_data"),
    [
        ("XBTUSD", CDCA_TEST_DATA["XBTUSD"]),
        ("AAPLxUSD", CDCA_TEST_DATA["AAPLxUSD"]),
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
