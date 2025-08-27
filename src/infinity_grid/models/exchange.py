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

    # General
    EXCHANGE: str

    # Order sides
    BUY: str
    SELL: str

    # Order states
    OPEN: str
    CLOSED: str
    CANCELED: str
    EXPIRED: str
    PENDING: str


class AssetPairInfoSchema(BaseModel):
    """Model for required asset pair information"""

    base: str  # "XXBT"
    quote: str  # "ZUSD"
    cost_decimals: int  # Number of decimals for cost, e.g. 5
    # Fees for maker orders, e.g. [[0, 0.25], [10000, 0.2], ...]
    fees_maker: list[list[float]] = Field(..., description="Maker fees structure")


class OrderInfoSchema(BaseModel):
    """Model for order information"""

    pair: str = Field(
        ...,
        min_length=1,
        description="Asset pair name",
    )  # altname without "/"
    price: float = Field(..., gt=0, description="Order price")
    side: str = Field(..., description="Order side (buy/sell)")
    status: str = Field(
        ...,
        description="Order status",
    )  # e.g. "open", "closed", "canceled"
    txid: str = Field(..., min_length=1, description="Transaction ID")
    userref: int = Field(..., ge=0, description="User reference number")
    vol_exec: float = Field(..., ge=0, description="Volume executed")
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
    base_balance: float = Field(..., ge=0, description="Base asset balance")
    quote_balance: float = Field(..., ge=0, description="Quote asset balance")
    base_available: float = Field(..., ge=0, description="Available base asset balance")
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

    asset: str = Field(..., min_length=1, description="Asset name")  # e.g. "XXBT"
    balance: float = Field(..., ge=0, description="Current balance of the asset")
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
    """Model for the response of a create order operation"""

    txid: str = Field(
        ...,
        min_length=1,
        description="Transaction ID of the created order",
    )


class TickerUpdateSchema(BaseModel):
    """Model for ticker update data"""

    symbol: str = Field(..., min_length=1, description="Trading pair symbol")
    last: float = Field(..., gt=0, description="Last traded price")


class ExecutionsUpdateSchema(BaseModel):
    """Model for execution update data"""

    order_id: str = Field(..., min_length=1, description="Order ID")
    exec_type: str = Field(
        ...,
        description="Execution type",
    )  # e.g. "new", "filled", "cancelled"


class OnMessageSchema(BaseModel):
    """Model for WebSocket message data"""

    channel: str = Field(
        ...,
        min_length=1,
        description="Message channel",
    )  # "ticker" or "executions"
    type: str | None = Field(None, description="Message type")  # "update" or "snapshot"
    ticker_data: TickerUpdateSchema | None = None
    executions: list[ExecutionsUpdateSchema] | None = None
