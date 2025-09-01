# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Exchange models and schemas for the Infinity Grid trading bot.

This module contains Pydantic models that define the structure and validation
rules for exchange-related data such as orders, balances, and market updates.
All schemas include appropriate validators to ensure data integrity.
"""
from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator


class ExchangeDomain(BaseModel):
    """
    Basic information on how exchange-specific naming conventions.
    """

    # General
    EXCHANGE: str  #: The name of the exchange

    # Order sides
    BUY: str  #: How the "buy" or "long" side is named
    SELL: str  #: How the "sell" or "short" side is named

    # Order states
    OPEN: str  #: How the order state "open" is named
    CLOSED: str  #: How the order state "closed" is named
    CANCELED: str  #: How the order state "canceled" is named
    EXPIRED: str  #: How the order state "expired" is named
    PENDING: str  #: How the order state "pending" is named


class AssetPairInfoSchema(BaseModel):
    """Schema for required asset pair information"""

    base: str  #: The base currency, e.g. "XXBT"
    quote: str  #: The quote currency, e.g. "ZUSD"

    cost_decimals: int  #: Number of decimals for cost, e.g. 5
    #: Fees for maker orders, e.g. [[0, 0.25], [10000, 0.2], ...]
    fees_maker: list[list[float]] = Field(..., description="Maker fees structure")


class OrderInfoSchema(BaseModel):
    """Schema for order information"""

    #: Asset pair name (altname) without "/", e.g. BTCUSD
    pair: str = Field(
        ...,
        min_length=1,
        description="Asset pair name",
    )
    price: float = Field(..., gt=0, description="Order price")  #: The order price
    side: str = Field(..., description="Order side (buy/sell)")  #: The order side
    #: The order status e.g. "open", "closed", "canceled"
    status: str = Field(
        ...,
        description="Order status",
    )
    #: The transaction ID
    txid: str = Field(..., min_length=1, description="Transaction ID")
    #: The user reference number of the order
    userref: int = Field(..., ge=0, description="User reference number")
    #: The executed volume of the order
    vol_exec: float = Field(..., ge=0, description="Volume executed")
    #: The volume of the order
    vol: float = Field(..., gt=0, description="Total volume of the order")

    @model_validator(mode="after")
    def validate_volume_relationship(self: Self) -> Self:
        """Validate that executed volume doesn't exceed total volume"""
        if self.vol_exec > self.vol:
            raise ValueError(
                f"Executed volume ({self.vol_exec}) cannot exceed total volume ({self.vol})",
            )
        return self

    @field_validator("pair")
    def clean_pair(cls: OrderInfoSchema, v: str) -> str:  # noqa: N805
        """
        Remove any '/' characters from the pair field

        Ensuring that the pair is always the "altname", e.g. "XBT/USD" will be
        transformed to "XBTUSD". This is necessary for consistency
        across different parts of the application that expect the pair without
        slashes.
        """
        return v.replace("/", "")


class PairBalanceSchema(BaseModel):
    """
    A schema required for providing information about total and available
    assets.
    """

    #: The current balance (total) of the base currency
    base_balance: float = Field(..., ge=0, description="Base asset balance")
    #: The current balance (total) of the quote currency
    quote_balance: float = Field(..., ge=0, description="Quote asset balance")
    #: The available balance of the base currency
    base_available: float = Field(..., ge=0, description="Available base asset balance")
    #: The available balance of the quote currency
    quote_available: float = Field(
        ...,
        ge=0,
        description="Available quote asset balance",
    )

    @model_validator(mode="after")
    def validate_available_balances(self) -> Self:
        """Validate that available balances don't exceed total balances"""
        if self.base_available > self.base_balance:
            raise ValueError(
                f"Available base balance ({self.base_available}) cannot exceed total base balance ({self.base_balance})",
            )
        if self.quote_available > self.quote_balance:
            raise ValueError(
                f"Available quote balance ({self.quote_available}) cannot exceed total quote balance ({self.quote_balance})",
            )
        return self


class AssetBalanceSchema(BaseModel):
    """Schema for a single asset balance."""

    #: The asset name
    asset: str = Field(..., min_length=1, description="Asset name")
    #: The total balance of the asset
    balance: float = Field(..., ge=0, description="Current balance of the asset")
    #: The balance of an asset that is held in trades
    hold_trade: float = Field(..., ge=0, description="Balance held in trades")

    @model_validator(mode="after")
    def validate_hold_trade(self) -> Self:
        """Validate that held balance doesn't exceed total balance"""
        if self.hold_trade > self.balance:
            raise ValueError(
                f"Held balance ({self.hold_trade}) cannot exceed total balance ({self.balance})",
            )
        return self


class CreateOrderResponseSchema(BaseModel):
    """Schema for the response of a create order operation"""

    #: The transaction ID of an order or trade
    txid: str = Field(
        ...,
        min_length=1,
        description="Transaction ID of the created order",
    )


class TickerUpdateSchema(BaseModel):
    """Schema for ticker update data"""

    #: The trading pair symbol of the ticker
    symbol: str = Field(..., min_length=1, description="Trading pair symbol")
    #: The last traded price of a trading pair based on this ticker
    last: float = Field(..., gt=0, description="Last traded price")


class ExecutionsUpdateSchema(BaseModel):
    """Schema for execution update data"""

    #: The order ID
    order_id: str = Field(..., min_length=1, description="Order ID")
    #: The execution type, e.g. "new", "filled", "cancelled"
    exec_type: str = Field(..., description="Execution type")


class OnMessageSchema(BaseModel):
    """Schema for WebSocket message data"""

    #: The channel of the message, e.g. "ticker" or "executions"
    channel: str = Field(
        ...,
        min_length=1,
        description="Message channel",
    )
    #: Type of the message, e.g. "update" or "snapshot"
    type: str | None = Field(None, description="Message type")
    #: The ticker data
    ticker_data: TickerUpdateSchema | None = None
    #: Any executions
    executions: list[ExecutionsUpdateSchema] | None = None
