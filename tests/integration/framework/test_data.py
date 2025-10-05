# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Test data models and parameterization for integration tests.

This module provides structured data models for test expectations and
parameterization, making it easier to maintain test data and extend
to new exchanges and trading pairs.
"""

from typing import Any
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


class CDCATestExpectations(BaseModel):
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
# cDCA Strategy Test Data
# =============================================================================

CDCA_XBTUSD_EXPECTATIONS = CDCATestExpectations(
    initial_ticker=50_000.0,
    check_initial_n_buy_orders=OrderExpectation(
        prices=(
            49_504.9,
            49_014.7,
            48_529.4,
            48_048.9,
            47_573.1,
        ),
        volumes=(
            0.00202,
            0.0020402,
            0.0020606,
            0.00208121,
            0.00210202,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    trigger_shift_up_buy_orders=ShiftOrdersExpectation(
        new_price=60_000.0,
        prices=(
            59_405.9,
            58_817.7,
            58_235.3,
            57_658.7,
            57_087.8,
        ),
        volumes=(
            0.00168333,
            0.00170016,
            0.00171717,
            0.00173434,
            0.00175168,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    trigger_fill_buy_order=FillBuyOrderExpectation(
        no_trigger_price=59_990.0,
        new_price=59_000.0,
        old_prices=(
            59_405.9,
            58_817.7,
            58_235.3,
            57_658.7,
            57_087.8,
        ),
        old_volumes=(
            0.00168333,
            0.00170016,
            0.00171717,
            0.00173434,
            0.00175168,
        ),
        old_sides=("buy", "buy", "buy", "buy", "buy"),
        new_prices=(
            58_817.7,
            58_235.3,
            57_658.7,
            57_087.8,
        ),
        new_volumes=(
            0.00170016,
            0.00171717,
            0.00173434,
            0.00175168,
        ),
        new_sides=("buy", "buy", "buy", "buy"),
    ),
    trigger_ensure_n_open_buy_orders=ShiftOrdersExpectation(
        new_price=59_100.0,
        prices=(58_817.7, 58_235.3, 57_658.7, 57_087.8, 56_522.5),
        volumes=(
            0.00170016,
            0.00171717,
            0.00173434,
            0.00175168,
            0.0017692,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    trigger_rapid_price_drop=RapidPriceDropExpectation(
        new_price=50_000.0,
        prices=(),
        volumes=(),
        sides=(),
    ),
    trigger_ensure_n_open_buy_orders_after_drop=ShiftOrdersExpectation(
        new_price=50_100.0,
        prices=(
            49_603.9,
            49_112.7,
            48_626.4,
            48_144.9,
            47_668.2,
        ),
        volumes=(
            0.00201597,
            0.00203613,
            0.00205649,
            0.00207706,
            0.00209783,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    check_max_investment_reached=MaxInvestmentExpectation(
        current_price=50_000.0,
        n_open_sell_orders=0,
        max_investment=50.0,
    ),
)

CDCA_AAPLXUSD_EXPECTATIONS = CDCATestExpectations(
    initial_ticker=260.0,
    check_initial_n_buy_orders=OrderExpectation(
        prices=(257.42, 254.87, 252.34, 249.84, 247.36),
        volumes=(
            0.3884702,
            0.39235688,
            0.39629071,
            0.40025616,
            0.40426908,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    trigger_shift_up_buy_orders=ShiftOrdersExpectation(
        new_price=280.0,
        prices=(277.22, 274.47, 271.75, 269.05, 266.38),
        volumes=(
            0.36072433,
            0.36433854,
            0.36798528,
            0.37167812,
            0.37540355,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    trigger_fill_buy_order=FillBuyOrderExpectation(
        no_trigger_price=279.0,
        new_price=277.0,
        old_prices=(277.22, 274.47, 271.75, 269.05, 266.38),
        old_volumes=(
            0.36072433,
            0.36433854,
            0.36798528,
            0.37167812,
            0.37540355,
        ),
        old_sides=("buy", "buy", "buy", "buy", "buy"),
        new_prices=(274.47, 271.75, 269.05, 266.38),
        new_volumes=(
            0.36433854,
            0.36798528,
            0.37167812,
            0.37540355,
        ),
        new_sides=("buy", "buy", "buy", "buy"),
    ),
    trigger_ensure_n_open_buy_orders=ShiftOrdersExpectation(
        new_price=277.1,
        prices=(274.47, 271.75, 269.05, 266.38, 263.74),
        volumes=(
            0.36433854,
            0.36798528,
            0.37167812,
            0.37540355,
            0.37916129,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    trigger_rapid_price_drop=RapidPriceDropExpectation(
        new_price=260.0,
        prices=(),
        volumes=(),
        sides=(),
    ),
    trigger_ensure_n_open_buy_orders_after_drop=ShiftOrdersExpectation(
        new_price=260.0,
        prices=(257.42, 254.87, 252.34, 249.84, 247.36),
        volumes=(
            0.3884702,
            0.39235688,
            0.39629071,
            0.40025616,
            0.40426908,
        ),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    check_max_investment_reached=MaxInvestmentExpectation(
        current_price=260.0,
        n_open_sell_orders=0,
        max_investment=50.0,
    ),
)

# Test data mapping for easy access
CDCA_TEST_DATA = {
    "XBTUSD": CDCA_XBTUSD_EXPECTATIONS,
    "AAPLxUSD": CDCA_AAPLXUSD_EXPECTATIONS,
}

