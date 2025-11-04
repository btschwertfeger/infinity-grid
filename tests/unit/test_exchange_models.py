# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Test module for exchange models and schemas.

This module contains focused tests for the most critical aspects of
Pydantic models defined in infinity_grid.models.exchange.
"""

import pytest
from pydantic import ValidationError

from infinity_grid.models.exchange import (
    AssetBalanceSchema,
    AssetPairInfoSchema,
    CreateOrderResponseSchema,
    ExchangeDomain,
    ExecutionsUpdateSchema,
    OnMessageSchema,
    OrderInfoSchema,
    PairBalanceSchema,
    TickerUpdateSchema,
)


class TestExchangeDomain:
    """Test cases for ExchangeDomain model"""

    def test_valid_exchange_domain(self) -> None:
        """Test creating a valid ExchangeDomain instance"""
        domain = ExchangeDomain(
            EXCHANGE="kraken",
            BUY="buy",
            SELL="sell",
            OPEN="open",
            CLOSED="closed",
            CANCELED="canceled",
            EXPIRED="expired",
            PENDING="pending",
        )
        assert domain.EXCHANGE == "kraken"
        assert domain.BUY == "buy"
        assert domain.SELL == "sell"

    def test_missing_required_fields(self) -> None:
        """Test that missing required fields raise ValidationError"""
        with pytest.raises(ValidationError):
            ExchangeDomain()


class TestAssetPairInfoSchema:
    """Test cases for AssetPairInfoSchema model"""

    def test_valid_asset_pair_info(self) -> None:
        """Test creating a valid AssetPairInfoSchema instance"""
        pair_info = AssetPairInfoSchema(
            base="XXBT",
            quote="ZUSD",
            cost_decimals=5,
            lot_decimals=8,
            fees_maker=[[0, 0.25], [10000, 0.2]],
            aclass_base="currency",
            aclass_quote="currency",
        )
        assert pair_info.base == "XXBT"
        assert pair_info.quote == "ZUSD"
        assert pair_info.cost_decimals == 5

    def test_empty_fees_maker(self) -> None:
        """Test that empty fees_maker list is valid"""
        pair_info = AssetPairInfoSchema(
            base="ETH",
            quote="USD",
            cost_decimals=2,
            lot_decimals=8,
            fees_maker=[],
            aclass_base="currency",
            aclass_quote="currency",
        )
        assert pair_info.fees_maker == []


class TestOrderInfoSchema:
    """Test cases for OrderInfoSchema model"""

    def test_valid_order_info(self) -> None:
        """Test creating a valid OrderInfoSchema instance"""
        order = OrderInfoSchema(
            status="open",
            vol_exec=0.5,
            vol=1.0,
            pair="XXBTZUSD",
            userref=12345,
            txid="ABCDEF-123456",
            price=50000.0,
            side="buy",
        )
        assert order.vol_exec == 0.5
        assert order.vol == 1.0
        assert order.price == 50000.0

    def test_volume_validation(self) -> None:
        """Test that executed volume cannot exceed total volume"""
        with pytest.raises(ValidationError, match="cannot exceed total volume"):
            OrderInfoSchema(
                status="open",
                vol_exec=1.5,  # Exceeds vol
                vol=1.0,
                pair="BTCUSD",
                userref=123,
                txid="TX123",
                price=50000.0,
                side="buy",
            )

    def test_negative_values_fail(self) -> None:
        """Test that negative values fail validation"""
        with pytest.raises(ValidationError):
            OrderInfoSchema(
                status="open",
                vol_exec=-0.1,  # Negative
                vol=1.0,
                pair="BTCUSD",
                userref=123,
                txid="TX123",
                price=50000.0,
                side="buy",
            )

    def test_zero_price_fails(self) -> None:
        """Test that zero price fails validation"""
        with pytest.raises(ValidationError):
            OrderInfoSchema(
                status="open",
                vol_exec=0.0,
                vol=1.0,
                pair="BTCUSD",
                userref=123,
                txid="TX123",
                price=0.0,  # Invalid
                side="buy",
            )


class TestPairBalanceSchema:
    """Test cases for PairBalanceSchema model"""

    def test_valid_pair_balance(self) -> None:
        """Test creating a valid PairBalanceSchema instance"""
        balance = PairBalanceSchema(
            base_balance=1.5,
            quote_balance=75000.0,
            base_available=1.0,
            quote_available=50000.0,
        )
        assert balance.base_balance == 1.5
        assert balance.quote_balance == 75000.0

    def test_negative_balances_fail(self) -> None:
        """Test that negative balances fail validation"""
        with pytest.raises(ValidationError):
            PairBalanceSchema(
                base_balance=-1.0,  # Negative
                quote_balance=50000.0,
                base_available=0.0,
                quote_available=25000.0,
            )


class TestAssetBalanceSchema:
    """Test cases for AssetBalanceSchema model"""

    def test_valid_asset_balance(self) -> None:
        """Test creating a valid AssetBalanceSchema instance"""
        asset_balance = AssetBalanceSchema(
            asset="XXBT",
            balance=2.5,
            hold_trade=0.5,
        )
        assert asset_balance.asset == "XXBT"
        assert asset_balance.balance == 2.5

    def test_empty_asset_fails(self) -> None:
        """Test that empty asset name fails validation"""
        with pytest.raises(ValidationError):
            AssetBalanceSchema(asset="", balance=1.0, hold_trade=0.0)


class TestTickerUpdateSchema:
    """Test cases for TickerUpdateSchema model"""

    def test_valid_ticker_update(self) -> None:
        """Test creating a valid TickerUpdateSchema instance"""
        ticker = TickerUpdateSchema(symbol="BTC/USD", last=50000.0)
        assert ticker.symbol == "BTC/USD"
        assert ticker.last == 50000.0

    def test_zero_price_fails(self) -> None:
        """Test that zero price fails validation"""
        with pytest.raises(ValidationError):
            TickerUpdateSchema(symbol="BTC/USD", last=0.0)


class TestExecutionsUpdateSchema:
    """Test cases for ExecutionsUpdateSchema model"""

    def test_valid_executions_update(self) -> None:
        """Test creating a valid ExecutionsUpdateSchema instance"""
        execution = ExecutionsUpdateSchema(order_id="ORDER-123", exec_type="filled")
        assert execution.order_id == "ORDER-123"
        assert execution.exec_type == "filled"

    def test_empty_order_id_fails(self) -> None:
        """Test that empty order_id fails validation"""
        with pytest.raises(ValidationError):
            ExecutionsUpdateSchema(order_id="", exec_type="new")


class TestOnMessageSchema:
    """Test cases for OnMessageSchema model"""

    def test_ticker_message(self) -> None:
        """Test creating a ticker message"""
        ticker_data = TickerUpdateSchema(symbol="BTC/USD", last=50000.0)
        message = OnMessageSchema(
            channel="ticker",
            type="update",
            ticker_data=ticker_data,
        )
        assert message.channel == "ticker"
        assert message.ticker_data.symbol == "BTC/USD"

    def test_executions_message(self) -> None:
        """Test creating an executions message"""
        executions = [ExecutionsUpdateSchema(order_id="ORDER-1", exec_type="filled")]
        message = OnMessageSchema(
            channel="executions",
            executions=executions,
        )
        assert message.channel == "executions"
        assert len(message.executions) == 1

    def test_empty_channel_fails(self) -> None:
        """Test that empty channel fails validation"""
        with pytest.raises(ValidationError):
            OnMessageSchema(channel="")


class TestCreateOrderResponseSchema:
    """Test cases for CreateOrderResponseSchema model"""

    def test_valid_response(self) -> None:
        """Test creating a valid response"""
        response = CreateOrderResponseSchema(txid="ORDER-123")
        assert response.txid == "ORDER-123"

    def test_empty_txid_fails(self) -> None:
        """Test that empty txid fails validation"""
        with pytest.raises(ValidationError):
            CreateOrderResponseSchema(txid="")


class TestModelIntegration:
    """Integration tests for models working together"""

    def test_order_workflow(self) -> None:
        """Test a complete order workflow"""
        # Create order response
        create_response = CreateOrderResponseSchema(txid="ORDER-123")

        # Order info
        order_info = OrderInfoSchema(
            status="open",
            vol_exec=0.0,
            vol=1.0,
            pair="BTCUSD",
            userref=12345,
            txid=create_response.txid,
            price=50000.0,
            side="buy",
        )

        # Execution update
        execution_update = ExecutionsUpdateSchema(
            order_id=order_info.txid,
            exec_type="filled",
        )

        # Verify workflow consistency
        assert create_response.txid == order_info.txid == execution_update.order_id

    def test_balance_consistency(self) -> None:
        """Test balance consistency across models"""
        btc_balance = AssetBalanceSchema(asset="XXBT", balance=2.0, hold_trade=0.5)
        usd_balance = AssetBalanceSchema(
            asset="ZUSD",
            balance=100000.0,
            hold_trade=25000.0,
        )

        pair_balance = PairBalanceSchema(
            base_balance=btc_balance.balance,
            quote_balance=usd_balance.balance,
            base_available=btc_balance.balance - btc_balance.hold_trade,
            quote_available=usd_balance.balance - usd_balance.hold_trade,
        )

        assert pair_balance.base_available == 1.5
        assert pair_balance.quote_available == 75000.0
