# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Unit tests for the GridSell Strategy class."""

from typing import Self
from unittest import mock
from unittest.mock import Mock, patch

import pytest

from infinity_grid.strategies.grid_sell import GridSellStrategy


class TestGridSellStrategy:
    """Test cases for GridSellStrategy order price calculation methods."""

    @pytest.fixture
    def mock_strategy(
        self: Self,
        mock_config: mock.MagicMock,
        mock_dependencies: mock.MagicMock,
    ) -> GridSellStrategy:
        """Create a GridSell Strategy instance with mocked dependencies."""
        with (
            patch("infinity_grid.strategies.grid_base.Orderbook"),
            patch("infinity_grid.strategies.grid_base.Configuration"),
            patch("infinity_grid.strategies.grid_base.PendingTXIDs"),
            patch("infinity_grid.strategies.grid_base.UnsoldBuyOrderTXIDs"),
        ):
            strategy = GridSellStrategy(
                config=mock_config,
                event_bus=mock_dependencies["event_bus"],
                state_machine=mock_dependencies["state_machine"],
                db=mock_dependencies["db"],
            )

            strategy._configuration_table = Mock()
            strategy._configuration_table.get.return_value = {
                "price_of_highest_buy": 100.0,
            }
            strategy._orderbook_table = Mock()
            strategy._ticker = 50000.0

            return strategy

    def test_check_extra_sell_order_does_nothing(
        self: Self,
        mock_strategy: mock.MagicMock,
    ) -> None:
        """Test that check_extra_sell_order method does nothing (no-op)."""
        # FIXME: this is stupid
        mock_strategy._check_extra_sell_order()
