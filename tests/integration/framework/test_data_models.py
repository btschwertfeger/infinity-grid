# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Test data models for integration tests.

This module provides structured data models for test expectations and
parameterization, making it easier to maintain test data and extend
to new exchanges and trading pairs.
"""

from pydantic import BaseModel


class OrderExpectation(BaseModel):
    """Expected order characteristics."""

    prices: tuple[float, ...]
    volumes: tuple[float, ...]
    sides: tuple[str, ...]


class FillBuyOrderExpectation(BaseModel):
    """Expected behavior when filling a buy order."""

    no_trigger_price: float
    new_price: float
    old_prices: tuple[float, ...]
    old_volumes: tuple[float, ...]
    old_sides: tuple[str, ...]
    new_prices: tuple[float, ...]
    new_volumes: tuple[float, ...]
    new_sides: tuple[str, ...]


class ShiftOrdersExpectation(BaseModel):
    """Expected behavior when shifting orders."""

    new_price: float
    prices: tuple[float, ...]
    volumes: tuple[float, ...]
    sides: tuple[str, ...]


class RapidPriceDropExpectation(BaseModel):
    """Expected behavior during rapid price drops."""

    new_price: float
    prices: tuple[float, ...]
    volumes: tuple[float, ...]
    sides: tuple[str, ...]


class MaxInvestmentExpectation(BaseModel):
    """Expected behavior when max investment is reached."""

    current_price: float
    n_open_sell_orders: int
    max_investment: float


class FillSellOrderExpectation(BaseModel):
    """Expected behavior when filling a sell order."""

    new_price: float
    prices: tuple[float, ...]
    volumes: tuple[float, ...]
    sides: tuple[str, ...]


class TriggerAllSellOrdersExpectation(BaseModel):
    """Expected behavior when triggering all sell orders."""

    new_price: float
    buy_prices: tuple[float, ...]
    sell_prices: tuple[float, ...]
    buy_volumes: tuple[float, ...]
    sell_volumes: tuple[float, ...]


class NotEnoughFundsForSellExpectation(BaseModel):
    """Expected behavior when there are not enough funds for sell order."""

    sell_price: float
    n_orders: int
    n_sell_orders: int
    assume_base_available: float
    assume_quote_available: float


class SellAfterNotEnoughFundsExpectation(BaseModel):
    """Expected behavior after resolving insufficient funds for sell."""

    price: float
    n_orders: int
    sell_prices: tuple[float, ...]
    sell_volumes: tuple[float, ...]


class BalanceExpectation(BaseModel):
    """Expected balance state at a specific point in testing."""

    expected_base_balance: float
    expected_base_hold: float
    expected_quote_balance: float
    expected_quote_hold: float


class PartialFillExpectation(BaseModel):
    """Expected behavior for partial fill handling."""

    fill_volume: float
    n_open_orders: int
    expected_base_balance: float
    expected_quote_balance: float
    vol_of_unfilled_remaining_max_price: float


class SellPartialFillExpectation(BaseModel):
    """Expected behavior when selling partial fill surplus."""

    order_price: float
    n_open_orders: int
    expected_sell_price: float
    expected_sell_volume: float


# =============================================================================
# cDCA Strategy Test Data
# =============================================================================


class CDCATestData(BaseModel):
    """Complete set of expectations for cDCA strategy testing."""

    initial_ticker: float
    check_initial_n_buy_orders: OrderExpectation
    trigger_shift_up_buy_orders: ShiftOrdersExpectation
    trigger_fill_buy_order: FillBuyOrderExpectation
    trigger_ensure_n_open_buy_orders: ShiftOrdersExpectation
    trigger_rapid_price_drop: RapidPriceDropExpectation
    trigger_ensure_n_open_buy_orders_after_drop: ShiftOrdersExpectation
    check_max_investment_reached: MaxInvestmentExpectation


# =============================================================================
# GridHOLD Strategy Models and Test Data
# =============================================================================


class GridHODLTestData(BaseModel):
    """Complete set of expectations for GridHODL strategy testing."""

    initial_ticker: float
    check_initial_n_buy_orders: OrderExpectation
    trigger_shift_up_buy_orders: ShiftOrdersExpectation
    trigger_fill_buy_order: FillBuyOrderExpectation
    trigger_ensure_n_open_buy_orders: ShiftOrdersExpectation
    trigger_fill_sell_order: FillSellOrderExpectation
    trigger_rapid_price_drop: RapidPriceDropExpectation
    trigger_all_sell_orders: TriggerAllSellOrdersExpectation
    check_not_enough_funds_for_sell: NotEnoughFundsForSellExpectation
    sell_after_not_enough_funds_for_sell: SellAfterNotEnoughFundsExpectation
    check_max_investment_reached: MaxInvestmentExpectation


# =============================================================================
# GridHOLD Unfilled Surplus Test Data
# =============================================================================


class GridHODLUnfilledSurplusTestData(BaseModel):
    """Complete set of expectations for GridHODL unfilled surplus testing."""

    initial_ticker: float
    check_initial_n_buy_orders: OrderExpectation
    partial_fill: PartialFillExpectation
    sell_partial_fill: SellPartialFillExpectation


# =============================================================================
# GridSell Strategy Models and Test Data
# =============================================================================


class GridSellTestData(BaseModel):
    """Complete set of expectations for GridSell strategy testing."""

    initial_ticker: float
    check_initial_n_buy_orders: OrderExpectation
    trigger_shift_up_buy_orders: ShiftOrdersExpectation
    trigger_fill_buy_order: FillBuyOrderExpectation
    trigger_ensure_n_open_buy_orders: ShiftOrdersExpectation
    trigger_fill_sell_order: FillSellOrderExpectation
    trigger_rapid_price_drop: RapidPriceDropExpectation
    trigger_all_sell_orders: TriggerAllSellOrdersExpectation
    check_max_investment_reached: MaxInvestmentExpectation
    trigger_ensure_n_open_buy_orders_after_max_investment: ShiftOrdersExpectation
    check_not_enough_funds_for_sell: NotEnoughFundsForSellExpectation


class GridSellUnfilledSurplusTestData(BaseModel):
    """Complete set of expectations for GridSell unfilled surplus testing."""

    initial_ticker: float
    check_initial_n_buy_orders: OrderExpectation
    partial_fill: PartialFillExpectation
    sell_partial_fill: SellPartialFillExpectation


# =============================================================================
# SWING Strategy Test Data
# =============================================================================


class SWINGTestData(BaseModel):
    """Complete set of expectations for SWING strategy testing."""

    initial_ticker: float
    check_initial_n_buy_orders: OrderExpectation
    trigger_rapid_price_drop: RapidPriceDropExpectation
    trigger_ensure_n_open_buy_orders: ShiftOrdersExpectation
    trigger_shift_up_buy_orders: ShiftOrdersExpectation
    check_not_enough_funds_for_sell: NotEnoughFundsForSellExpectation


class SWINGUnfilledSurplusTestData(BaseModel):
    """Complete set of expectations for SWING unfilled surplus testing."""

    initial_ticker: float
    check_initial_n_buy_orders: OrderExpectation
    initial_balances: BalanceExpectation
    partial_fill: PartialFillExpectation
    partial_fill_balances: BalanceExpectation
    sell_partial_fill: SellPartialFillExpectation
    check_max_investment_reached: MaxInvestmentExpectation
