# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#


from typing import Self
from unittest import mock
from unittest.mock import Mock, patch

import pytest

from infinity_grid.strategies.c_dca import CDCAStrategy
from infinity_grid.strategies.grid_base import GridStrategyBase
from infinity_grid.strategies.grid_hodl import GridHODLStrategy
from infinity_grid.strategies.grid_sell import GridSellStrategy
from infinity_grid.strategies.swing import SwingStrategy


class TestGridBaseBuyOrderPrice:
    """Test cases for buy order price calculation methods."""

    # Using all classes to ensure they behave uniformly
    @pytest.fixture(
        params=[
            CDCAStrategy,
            GridHODLStrategy,
            GridSellStrategy,
            GridStrategyBase,
            SwingStrategy,
        ],
    )
    def strategy_class(self: Self, request: pytest.FixtureRequest) -> mock.MagicMock:
        """Parametrized fixture providing different strategy classes."""
        return request.param

    @pytest.fixture
    def mock_strategy(
        self: Self,
        strategy_class: mock.MagicMock,
        mock_config: mock.MagicMock,
        mock_dependencies: mock.MagicMock,
    ) -> mock.MagicMock:
        """Create a Strategy instance with mocked dependencies."""
        with (
            patch("infinity_grid.strategies.grid_base.Orderbook"),
            patch("infinity_grid.strategies.grid_base.Configuration"),
            patch("infinity_grid.strategies.grid_base.PendingTXIDs"),
            patch("infinity_grid.strategies.grid_base.UnsoldBuyOrderTXIDs"),
        ):
            strategy = strategy_class(
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

    def test_get_buy_order_price_normal_case(
        self: Self,
        mock_strategy: mock.MagicMock,
    ) -> None:
        """Test buy order price calculation for normal market conditions."""
        last_price = 50000.0
        expected_price = 47619.047619047619
        result = mock_strategy._get_buy_order_price(last_price)

        assert result == pytest.approx(expected_price, rel=1e-4)
        assert result < last_price  # Buy order should be below market price

    def test_get_buy_order_price_above_ticker(
        self: Self,
        mock_strategy: mock.MagicMock,
    ) -> None:
        """Test buy order price calculation when calculated price exceeds ticker."""
        # Set a high last_price that would make the calculated order_price > ticker
        last_price = 60000.0  # Higher than ticker (50000.0)
        expected_price = 47619.047619047619

        result = mock_strategy._get_buy_order_price(last_price)
        assert result == pytest.approx(expected_price, rel=1e-4)
        assert result < mock_strategy._ticker

    def test_get_buy_order_price_different_intervals(
        self: Self,
        strategy_class: mock.MagicMock,
        mock_config: mock.MagicMock,
        mock_dependencies: mock.MagicMock,
    ) -> None:
        """Test buy order price calculation with different interval values."""
        test_cases = [
            (0.01, 50000.0, 49504.9504950495),
            (0.10, 52000.0, 47272.72727272727),
            (0.20, 48000.0, 40000.0),
        ]

        for interval, last_price, expected_price in test_cases:
            mock_config.interval = interval

            with (
                patch("infinity_grid.strategies.grid_base.Orderbook"),
                patch("infinity_grid.strategies.grid_base.Configuration"),
                patch("infinity_grid.strategies.grid_base.PendingTXIDs"),
                patch("infinity_grid.strategies.grid_base.UnsoldBuyOrderTXIDs"),
            ):
                strategy = strategy_class(
                    config=mock_config,
                    event_bus=mock_dependencies["event_bus"],
                    state_machine=mock_dependencies["state_machine"],
                    db=mock_dependencies["db"],
                )
                strategy._configuration_table = Mock()
                strategy._ticker = 50000.0

                result = strategy._get_buy_order_price(last_price)
                assert result == pytest.approx(expected_price, rel=1e-4)
                assert result < last_price


class TestGridBaseSellOrderPrice:
    """Test cases for sell order price calculation methods."""

    # Using all classes to ensure they behave uniformly
    @pytest.fixture(
        params=[
            GridHODLStrategy,
            GridSellStrategy,
            GridStrategyBase,
            SwingStrategy,
        ],
    )
    def strategy_class(self: Self, request: pytest.FixtureRequest) -> mock.MagicMock:
        """Parametrized fixture providing different strategy classes."""
        return request.param

    @pytest.fixture
    def mock_strategy(
        self: Self,
        strategy_class: mock.MagicMock,
        mock_config: mock.MagicMock,
        mock_dependencies: mock.MagicMock,
    ) -> mock.MagicMock:
        """Create a Strategy instance with mocked dependencies."""
        with (
            patch("infinity_grid.strategies.grid_base.Orderbook"),
            patch("infinity_grid.strategies.grid_base.Configuration"),
            patch("infinity_grid.strategies.grid_base.PendingTXIDs"),
            patch("infinity_grid.strategies.grid_base.UnsoldBuyOrderTXIDs"),
        ):
            strategy = strategy_class(
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

    def test_get_sell_order_price_normal_case(
        self: Self,
        mock_strategy: mock.MagicMock,
    ) -> None:
        """Test sell order price calculation for normal market conditions."""
        last_price = 50000.0
        expected_price = 52500.0  # 50000 * (1 + interval)
        result = mock_strategy._get_sell_order_price(last_price)

        assert result == pytest.approx(expected_price, rel=1e-4)
        assert result > last_price  # Sell order should be above market price

    def test_get_sell_order_price_below_ticker(
        self: Self,
        mock_strategy: mock.MagicMock,
    ) -> None:
        """Test sell order price calculation when calculated price is below ticker."""
        # Set a low last_price that would make the calculated order_price < ticker
        last_price = 40000.0  # Lower than ticker (50000.0)
        expected_price = 52500.0  # ticker * (1 + interval)

        result = mock_strategy._get_sell_order_price(last_price)
        assert result == pytest.approx(expected_price, rel=1e-4)
        assert result > mock_strategy._ticker

    def test_get_sell_order_price_different_intervals(
        self: Self,
        mock_config: mock.MagicMock,
        mock_dependencies: mock.MagicMock,
    ) -> None:
        """Test sell order price calculation with different interval values."""
        test_cases = [
            (0.01, 50000.0, 50500.0),  # 1% interval
            (0.10, 52000.0, 57200.0),  # 10% interval
            (0.20, 48000.0, 57600.0),  # 20% interval
        ]

        for interval, last_price, expected_price in test_cases:
            mock_config.interval = interval

            with (
                patch("infinity_grid.strategies.grid_base.Orderbook"),
                patch("infinity_grid.strategies.grid_base.Configuration"),
                patch("infinity_grid.strategies.grid_base.PendingTXIDs"),
                patch("infinity_grid.strategies.grid_base.UnsoldBuyOrderTXIDs"),
            ):
                strategy = GridHODLStrategy(
                    config=mock_config,
                    event_bus=mock_dependencies["event_bus"],
                    state_machine=mock_dependencies["state_machine"],
                    db=mock_dependencies["db"],
                )
                strategy._configuration_table = Mock()
                strategy._configuration_table.get.return_value = {
                    "price_of_highest_buy": 60_000.0,
                }
                strategy._ticker = 50000.0

                result = strategy._get_sell_order_price(last_price)
                assert result == pytest.approx(expected_price, rel=1e-4)
                assert result > last_price

    def test_get_sell_order_price_updates_highest_buy_price(
        self: Self,
        mock_strategy: mock.MagicMock,
    ) -> None:
        """Test that sell order price method updates the highest buy price when appropriate."""
        # Set initial highest buy price lower than current price
        mock_strategy._configuration_table.get.return_value = {
            "price_of_highest_buy": 45000.0,
        }
        last_price = 50000.0

        mock_strategy._get_sell_order_price(last_price)

        # Should update the highest buy price
        mock_strategy._configuration_table.update.assert_called_once_with(
            {"price_of_highest_buy": last_price},
        )

    def test_get_sell_order_price_no_update_when_price_lower(
        self: Self,
        mock_strategy: mock.MagicMock,
    ) -> None:
        """Test that highest buy price is not updated when current price is lower."""
        # Set initial highest buy price higher than current price
        mock_strategy._configuration_table.get.return_value = {
            "price_of_highest_buy": 55000.0,
        }
        last_price = 50000.0

        mock_strategy._get_sell_order_price(last_price)

        # Should not update the highest buy price
        mock_strategy._configuration_table.update.assert_not_called()

    def test_new_sell_order_dry_run(self: Self, mock_strategy: mock.MagicMock) -> None:
        """Test new_sell_order method in dry run mode."""
        mock_strategy._config.dry_run = True
        try:
            mock_strategy._new_sell_order(50000.0)
        except NotImplementedError:
            pytest.skip("Strategy does not implement _get_sell_order_price")

        # Should not interact with orderbook table
        mock_strategy._orderbook_table.remove.assert_not_called()

    def test_new_sell_order_with_txid_to_delete(
        self: Self,
        mock_strategy: mock.MagicMock,
    ) -> None:
        """Test new_sell_order method with transaction ID to delete."""
        txid_to_delete = "test_txid_123"

        # Mock the unsold buy order txids table
        mock_strategy._unsold_buy_order_txids_table = Mock()
        mock_strategy._unsold_buy_order_txids_table.get.return_value.first.return_value = (
            None
        )

        # Mock the rest API for order retrieval
        mock_strategy._rest_api = Mock()
        mock_order = Mock()
        mock_order.status = "closed"
        mock_order.vol_exec = 0.001
        mock_strategy._rest_api.get_order_with_retry.return_value = mock_order
        mock_strategy._rest_api.truncate.side_effect = (
            lambda amount, **kwargs: amount  # noqa: ARG005
        )
        mock_strategy._rest_api.get_pair_balance.return_value.base_available = 1.0
        mock_strategy._rest_api.create_order.return_value.txid = "new_sell_order_txid"

        # Mock exchange domain
        mock_strategy._exchange_domain = Mock()
        mock_strategy._exchange_domain.CLOSED = "closed"
        mock_strategy._exchange_domain.SELL = "sell"

        # Mock pending txids table
        mock_strategy._pending_txids_table = Mock()

        # Mock assign order method
        mock_strategy._assign_order_by_txid = Mock()

        try:
            mock_strategy._new_sell_order(50000.0, txid_to_delete=txid_to_delete)
        except NotImplementedError:
            pytest.skip("Strategy does not implement _new_sell_order")

        # Should remove the specified transaction ID from orderbook
        mock_strategy._orderbook_table.remove.assert_called_once_with(
            filters={"txid": txid_to_delete},
        )
