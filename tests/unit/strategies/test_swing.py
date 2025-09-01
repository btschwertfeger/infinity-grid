# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Unit tests for the Swing Strategy class."""

from typing import Self
from unittest import mock
from unittest.mock import Mock, patch

import pytest

from infinity_grid.strategies.swing import SwingStrategy


class TestSwingStrategy:
    """Test cases for SwingStrategy order price calculation methods."""

    @pytest.fixture
    def mock_strategy(
        self: Self,
        mock_config: mock.MagicMock,
        mock_dependencies: mock.MagicMock,
    ) -> SwingStrategy:
        """Create a Swing Strategy instance with mocked dependencies."""
        with (
            patch("infinity_grid.strategies.grid_base.Orderbook"),
            patch("infinity_grid.strategies.grid_base.Configuration"),
            patch("infinity_grid.strategies.grid_base.PendingTXIDs"),
            patch("infinity_grid.strategies.grid_base.UnsoldBuyOrderTXIDs"),
        ):
            strategy = SwingStrategy(
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
            strategy._exchange_domain = Mock()
            strategy._exchange_domain.SELL = "sell"
            strategy._rest_api = Mock()
            strategy._amount_per_grid_plus_fee = 105.0
            strategy._event_bus = mock_dependencies["event_bus"]
            strategy._handle_arbitrage = Mock()
            return strategy

    def test_get_extra_sell_order_price_with_last_price_higher(
        self: Self,
        mock_strategy: SwingStrategy,
    ) -> None:
        """Test _get_extra_sell_order_price when last price is higher than highest buy."""
        # Given: last price of 120.0, highest buy of 100.0, interval of 5%
        last_price = 120.0
        mock_strategy._configuration_table.get.return_value = {
            "price_of_highest_buy": 100.0,
        }

        # When: calculating extra sell order price
        result = mock_strategy._get_extra_sell_order_price(last_price)

        # Then: should use last price with 2x interval
        assert result == 132.3

    def test_get_extra_sell_order_price_with_highest_buy_higher(
        self: Self,
        mock_strategy: SwingStrategy,
    ) -> None:
        """Test _get_extra_sell_order_price when highest buy is higher than calculated price."""
        # Given: last price of 80.0, highest buy of 100.0, interval of 5%
        last_price = 80.0
        mock_strategy._configuration_table.get.return_value = {
            "price_of_highest_buy": 100.0,
        }

        # When: calculating extra sell order price
        result = mock_strategy._get_extra_sell_order_price(last_price)

        # Then: should use highest buy price with 2x interval
        assert result == 110.25

    def test_get_extra_sell_order_price_with_string_input(
        self: Self,
        mock_strategy: SwingStrategy,
    ) -> None:
        """Test _get_extra_sell_order_price handles string input correctly."""
        # Given: last price as string
        last_price = "120.0"
        mock_strategy._configuration_table.get.return_value = {
            "price_of_highest_buy": 100.0,
        }

        # When: calculating extra sell order price
        result = mock_strategy._get_extra_sell_order_price(last_price)

        # Then: should convert to float and calculate correctly
        assert result == 132.3

    def test_check_extra_sell_order_no_sell_orders_sufficient_balance(
        self: Self,
        mock_strategy: SwingStrategy,
    ) -> None:
        """Test _check_extra_sell_order places order when conditions are met."""
        # Given: no existing sell orders and sufficient balance
        mock_strategy._orderbook_table.count.return_value = 0

        mock_balance = Mock()
        mock_balance.base_available = (
            2.0  # Enough for order (2.0 * 50000 = 100000 > 105)
        )
        mock_strategy._rest_api.get_pair_balance.return_value = mock_balance

        # When: checking for extra sell order
        mock_strategy._check_extra_sell_order()

        # Then: should check orderbook, get balance, and place arbitrage order
        mock_strategy._orderbook_table.count.assert_called_once_with(
            filters={"side": "sell"},
        )
        mock_strategy._rest_api.get_pair_balance.assert_called_once()
        mock_strategy._handle_arbitrage.assert_called_once()
        mock_strategy._event_bus.publish.assert_called_once()

    def test_check_extra_sell_order_existing_sell_orders(
        self: Self,
        mock_strategy: SwingStrategy,
    ) -> None:
        """Test _check_extra_sell_order does nothing when sell orders exist."""
        # Given: existing sell orders
        mock_strategy._orderbook_table.count.return_value = 1

        # When: checking for extra sell order
        mock_strategy._check_extra_sell_order()

        # Then: should only check orderbook and return early
        mock_strategy._orderbook_table.count.assert_called_once_with(
            filters={"side": "sell"},
        )
        mock_strategy._rest_api.get_pair_balance.assert_not_called()
        mock_strategy._handle_arbitrage.assert_not_called()

    def test_check_extra_sell_order_insufficient_balance(
        self: Self,
        mock_strategy: SwingStrategy,
    ) -> None:
        """Test _check_extra_sell_order does nothing when balance is insufficient."""
        # Given: no existing sell orders but insufficient balance
        mock_strategy._orderbook_table.count.return_value = 0

        mock_balance = Mock()
        mock_balance.base_available = 0.001  # Not enough (0.001 * 50000 = 50 < 105)
        mock_strategy._rest_api.get_pair_balance.return_value = mock_balance

        # When: checking for extra sell order
        mock_strategy._check_extra_sell_order()

        # Then: should check orderbook and balance but not place order
        mock_strategy._orderbook_table.count.assert_called_once_with(
            filters={"side": "sell"},
        )
        mock_strategy._rest_api.get_pair_balance.assert_called_once()
        mock_strategy._handle_arbitrage.assert_not_called()

    def test_check_extra_sell_order_calls_get_extra_sell_order_price(
        self: Self,
        mock_strategy: SwingStrategy,
    ) -> None:
        """Test _check_extra_sell_order calls _get_extra_sell_order_price with correct params."""
        # Given: conditions met for placing order
        mock_strategy._orderbook_table.count.return_value = 0

        mock_balance = Mock()
        mock_balance.base_available = 2.0
        mock_strategy._rest_api.get_pair_balance.return_value = mock_balance

        # Mock the _get_extra_sell_order_price method
        with patch.object(
            mock_strategy,
            "_get_extra_sell_order_price",
        ) as mock_get_price:
            mock_get_price.return_value = 52500.0

            # When: checking for extra sell order
            mock_strategy._check_extra_sell_order()

            # Then: should call _get_extra_sell_order_price with ticker value
            mock_get_price.assert_called_once_with(last_price=50000.0)
            mock_strategy._handle_arbitrage.assert_called_once_with(
                side="sell",
                order_price=52500.0,
            )
