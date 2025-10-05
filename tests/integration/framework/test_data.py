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


# =============================================================================
# cDCA Strategy Test Data
# =============================================================================


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


# =============================================================================
# GridHOLD Strategy Models and Test Data
# =============================================================================


class GridHODLTestExpectations(BaseModel):
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


GRIDHODL_XBTUSD_EXPECTATIONS = GridHODLTestExpectations(
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
            59_999.9,
        ),
        new_volumes=(
            0.00170016,
            0.00171717,
            0.00173434,
            0.00175168,
            0.00167504,
        ),
        new_sides=("buy", "buy", "buy", "buy", "sell"),
    ),
    trigger_ensure_n_open_buy_orders=ShiftOrdersExpectation(
        new_price=59_100.0,
        prices=(
            58_817.7,
            58_235.3,
            57_658.7,
            57_087.8,
            59_999.9,
            56_522.5,
        ),
        volumes=(
            0.00170016,
            0.00171717,
            0.00173434,
            0.00175168,
            0.00167504,
            0.0017692,
        ),
        sides=("buy", "buy", "buy", "buy", "sell", "buy"),
    ),
    trigger_fill_sell_order=FillSellOrderExpectation(
        new_price=60_000.0,
        prices=(
            58_817.7,
            58_235.3,
            57_658.7,
            57_087.8,
            56_522.5,
        ),
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
        prices=(
            59_405.8,
            58_817.6,
            58_235.2,
            57_658.6,
            57_087.7,
        ),
        volumes=(
            0.00169179,
            0.00170871,
            0.0017258,
            0.00174306,
            0.00176049,
        ),
        sides=("sell", "sell", "sell", "sell", "sell"),
    ),
    trigger_all_sell_orders=TriggerAllSellOrdersExpectation(
        new_price=59_100.0,
        buy_prices=(
            58_514.8,
            57_935.4,
            57_361.7,
            56_793.7,
            56_231.3,
        ),
        sell_prices=(59_405.8,),
        buy_volumes=(
            0.00170896,
            0.00172606,
            0.00174332,
            0.00176075,
            0.00177836,
        ),
        sell_volumes=(0.00169179,),
    ),
    check_not_enough_funds_for_sell=NotEnoughFundsForSellExpectation(
        sell_price=58_500.0,
        n_orders=5,
        n_sell_orders=1,
        assume_base_available=0.0,
        assume_quote_available=1000.0,
    ),
    sell_after_not_enough_funds_for_sell=SellAfterNotEnoughFundsExpectation(
        price=58_500.0,
        n_orders=7,
        sell_prices=(59_405.8, 59_099.9),
        sell_volumes=(0.00169179, 0.00170055),
    ),
    check_max_investment_reached=MaxInvestmentExpectation(
        current_price=50_000.0,
        n_open_sell_orders=2,
        max_investment=202.0,
    ),
)

GRIDHODL_AAPLXUSD_EXPECTATIONS = GridHODLTestExpectations(
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
        new_prices=(274.47, 271.75, 269.05, 266.38, 279.99),
        new_volumes=(
            0.36433854,
            0.36798528,
            0.37167812,
            0.37540355,
            0.3570128,
        ),
        new_sides=("buy", "buy", "buy", "buy", "sell"),
    ),
    trigger_ensure_n_open_buy_orders=ShiftOrdersExpectation(
        new_price=277.1,
        prices=(
            274.47,
            271.75,
            269.05,
            266.38,
            279.99,
            263.74,
        ),
        volumes=(
            0.36433854,
            0.36798528,
            0.37167812,
            0.37540355,
            0.3570128,
            0.37916129,
        ),
        sides=("buy", "buy", "buy", "buy", "sell", "buy"),
    ),
    trigger_fill_sell_order=FillSellOrderExpectation(
        new_price=280.0,
        prices=(
            274.47,
            271.75,
            269.05,
            266.38,
            263.74,
        ),
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
        prices=(277.21, 274.46, 271.74, 269.04, 266.37),
        volumes=(
            0.3605931,
            0.36420613,
            0.36785168,
            0.37154332,
            0.37526754,
        ),
        sides=("sell", "sell", "sell", "sell", "sell"),
    ),
    trigger_all_sell_orders=TriggerAllSellOrdersExpectation(
        new_price=275.0,
        buy_prices=(
            272.27,
            269.57,
            266.9,
            264.25,
            261.63,
        ),
        sell_prices=(277.21,),
        buy_volumes=(
            0.36728247,
            0.37096116,
            0.37467216,
            0.37842951,
            0.38221916,
        ),
        sell_volumes=(0.3605931,),
    ),
    check_not_enough_funds_for_sell=NotEnoughFundsForSellExpectation(
        sell_price=272.0,
        n_orders=5,
        n_sell_orders=1,
        assume_base_available=0.0,
        assume_quote_available=1000.0,
    ),
    sell_after_not_enough_funds_for_sell=SellAfterNotEnoughFundsExpectation(
        price=272.0,
        n_orders=7,
        sell_prices=(277.21, 274.99),
        sell_volumes=(0.3605931, 0.36350418),
    ),
    check_max_investment_reached=MaxInvestmentExpectation(
        current_price=270.0,
        n_open_sell_orders=2,
        max_investment=202.0,
    ),
)

# Test data mapping for GridHOLD strategy
GRIDHODL_TEST_DATA = {
    "XBTUSD": GRIDHODL_XBTUSD_EXPECTATIONS,
    "AAPLxUSD": GRIDHODL_AAPLXUSD_EXPECTATIONS,
}


# =============================================================================
# GridHOLD Unfilled Surplus Test Data
# =============================================================================

class PartialFillExpectation(BaseModel):
    """Expected behavior for partial fill handling."""

    fill_volume: float
    n_open_orders: int
    expected_base_balance: float  # Using float instead of Decimal for simplicity
    expected_quote_balance: float
    vol_of_unfilled_remaining_max_price: float


class SellPartialFillExpectation(BaseModel):
    """Expected behavior when selling partial fill surplus."""

    order_price: float
    n_open_orders: int
    expected_sell_price: float
    expected_sell_volume: float


class GridHODLUnfilledSurplusTestExpectations(BaseModel):
    """Complete set of expectations for GridHODL unfilled surplus testing."""

    initial_ticker: float
    check_initial_n_buy_orders: OrderExpectation
    partial_fill: PartialFillExpectation
    sell_partial_fill: SellPartialFillExpectation


GRIDHODL_UNFILLED_SURPLUS_XBTUSD_EXPECTATIONS = GridHODLUnfilledSurplusTestExpectations(
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
    partial_fill=PartialFillExpectation(
        fill_volume=0.002,
        n_open_orders=5,
        expected_base_balance=100.002,
        expected_quote_balance=999_400.99,
        vol_of_unfilled_remaining_max_price=49_504.9,
    ),
    sell_partial_fill=SellPartialFillExpectation(
        order_price=49_504.9,
        n_open_orders=5,
        expected_sell_price=50_500.0,
        expected_sell_volume=0.00199014,
    ),
)

GRIDHODL_UNFILLED_SURPLUS_AAPLXUSD_EXPECTATIONS = GridHODLUnfilledSurplusTestExpectations(
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
    partial_fill=PartialFillExpectation(
        fill_volume=0.3,
        n_open_orders=5,
        expected_base_balance=100.3,
        expected_quote_balance=999422.77401,
        vol_of_unfilled_remaining_max_price=257.42,
    ),
    sell_partial_fill=SellPartialFillExpectation(
        order_price=257.42,
        n_open_orders=5,
        expected_sell_price=262.6,
        expected_sell_volume=0.38065504,
    ),
)

# Test data mapping for GridHOLD unfilled surplus strategy
GRIDHODL_UNFILLED_SURPLUS_TEST_DATA = {
    "XBTUSD": GRIDHODL_UNFILLED_SURPLUS_XBTUSD_EXPECTATIONS,
    "AAPLxUSD": GRIDHODL_UNFILLED_SURPLUS_AAPLXUSD_EXPECTATIONS,
}


# =============================================================================
# GridSell Strategy Models and Test Data
# =============================================================================


class GridSellTestExpectations(BaseModel):
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


GRIDSELL_XBTUSD_EXPECTATIONS = GridSellTestExpectations(
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
            59_999.9,
        ),
        new_volumes=(
            0.00170016,
            0.00171717,
            0.00173434,
            0.00175168,
            0.00168333,
        ),
        new_sides=("buy", "buy", "buy", "buy", "sell"),
    ),
    trigger_ensure_n_open_buy_orders=ShiftOrdersExpectation(
        new_price=59_100.0,
        prices=(
            58_817.7,
            58_235.3,
            57_658.7,
            57_087.8,
            59_999.9,
            56_522.5,
        ),
        volumes=(
            0.00170016,
            0.00171717,
            0.00173434,
            0.00175168,
            0.00168333,
            0.0017692,
        ),
        sides=("buy", "buy", "buy", "buy", "sell", "buy"),
    ),
    trigger_fill_sell_order=FillSellOrderExpectation(
        new_price=60_000.0,
        prices=(
            58_817.7,
            58_235.3,
            57_658.7,
            57_087.8,
            56_522.5,
        ),
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
        prices=(
            59_405.8,
            58_817.6,
            58_235.2,
            57_658.6,
            57_087.7,
        ),
        volumes=(
            0.00170016,
            0.00171717,
            0.00173434,
            0.00175168,
            0.0017692,
        ),
        sides=("sell", "sell", "sell", "sell", "sell"),
    ),
    trigger_all_sell_orders=TriggerAllSellOrdersExpectation(
        new_price=59_100.0,
        buy_prices=(
            58_514.8,
            57_935.4,
            57_361.7,
            56_793.7,
            56_231.3,
        ),
        sell_prices=(59_405.8,),
        buy_volumes=(
            0.00170896,
            0.00172606,
            0.00174332,
            0.00176075,
            0.00177836,
        ),
        sell_volumes=(0.00170016,),
    ),
    check_max_investment_reached=MaxInvestmentExpectation(
        current_price=50_000.0,
        n_open_sell_orders=1,
        max_investment=102.0,
    ),
    trigger_ensure_n_open_buy_orders_after_max_investment=ShiftOrdersExpectation(
        new_price=50_000.0,
        prices=(
            59_405.8,
            49_504.9,
            49_014.7,
            48_529.4,
            48_048.9,
            47_573.1,
        ),
        volumes=(
            0.00170016,
            0.00202,
            0.0020402,
            0.0020606,
            0.00208121,
            0.00210202,
        ),
        sides=("sell", "buy", "buy", "buy", "buy", "buy"),
    ),
    check_not_enough_funds_for_sell=NotEnoughFundsForSellExpectation(
        sell_price=49_504.8,
        n_orders=6,
        n_sell_orders=1,
        assume_base_available=0.0,
        assume_quote_available=1000.0,
    ),
)

GRIDSELL_AAPLXUSD_EXPECTATIONS = GridSellTestExpectations(
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
        new_prices=(274.47, 271.75, 269.05, 266.38, 279.99),
        new_volumes=(
            0.36433854,
            0.36798528,
            0.37167812,
            0.37540355,
            0.36072433,
        ),
        new_sides=("buy", "buy", "buy", "buy", "sell"),
    ),
    trigger_ensure_n_open_buy_orders=ShiftOrdersExpectation(
        new_price=277.1,
        prices=(274.47, 271.75, 269.05, 266.38, 279.99, 263.74),
        volumes=(
            0.36433854,
            0.36798528,
            0.37167812,
            0.37540355,
            0.36072433,
            0.37916129,
        ),
        sides=("buy", "buy", "buy", "buy", "sell", "buy"),
    ),
    trigger_fill_sell_order=FillSellOrderExpectation(
        new_price=280.0,
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
        prices=(277.21, 274.46, 271.74, 269.04, 266.37),
        volumes=(
            0.36433854,
            0.36798528,
            0.37167812,
            0.37540355,
            0.37916129,
        ),
        sides=("sell", "sell", "sell", "sell", "sell"),
    ),
    trigger_all_sell_orders=TriggerAllSellOrdersExpectation(
        new_price=275.0,
        buy_prices=(
            272.27,
            269.57,
            266.9,
            264.25,
            261.63,
        ),
        sell_prices=(277.21,),
        buy_volumes=(
            0.36728247,
            0.37096116,
            0.37467216,
            0.37842951,
            0.38221916,
        ),
        sell_volumes=(0.36433854,),
    ),
    check_max_investment_reached=MaxInvestmentExpectation(
        current_price=270.0,
        n_open_sell_orders=1,
        max_investment=102.0,
    ),
    trigger_ensure_n_open_buy_orders_after_max_investment=ShiftOrdersExpectation(
        new_price=270.0,
        prices=(
            277.21,
            267.32,
            264.67,
            262.04,
            259.44,
            256.87,
        ),
        volumes=(
            0.36433854,
            0.37408349,
            0.37782899,
            0.38162112,
            0.38544557,
            0.38930198,
        ),
        sides=("sell", "buy", "buy", "buy", "buy", "buy"),
    ),
    check_not_enough_funds_for_sell=NotEnoughFundsForSellExpectation(
        sell_price=277.21,
        n_orders=6,
        n_sell_orders=1,
        assume_base_available=0.0,
        assume_quote_available=1000.0,
    ),
)

# Test data mapping for GridSell strategy
GRIDSELL_TEST_DATA = {
    "XBTUSD": GRIDSELL_XBTUSD_EXPECTATIONS,
    "AAPLxUSD": GRIDSELL_AAPLXUSD_EXPECTATIONS,
}


# =============================================================================
# GridSell Unfilled Surplus Test Data
# =============================================================================


class GridSellUnfilledSurplusTestExpectations(BaseModel):
    """Complete set of expectations for GridSell unfilled surplus testing."""

    initial_ticker: float
    check_initial_n_buy_orders: OrderExpectation
    partial_fill: PartialFillExpectation
    sell_partial_fill: SellPartialFillExpectation


GRIDSELL_UNFILLED_SURPLUS_XBTUSD_EXPECTATIONS = GridSellUnfilledSurplusTestExpectations(
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
    partial_fill=PartialFillExpectation(
        fill_volume=0.002,
        n_open_orders=5,
        expected_base_balance=100.002,
        expected_quote_balance=999_400.99,
        vol_of_unfilled_remaining_max_price=49_504.9,
    ),
    sell_partial_fill=SellPartialFillExpectation(
        order_price=49_504.9,
        n_open_orders=5,
        expected_sell_price=50_500.0,
        expected_sell_volume=0.00199014,
    ),
)

GRIDSELL_UNFILLED_SURPLUS_AAPLXUSD_EXPECTATIONS = GridSellUnfilledSurplusTestExpectations(
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
    partial_fill=PartialFillExpectation(
        fill_volume=0.3,
        n_open_orders=5,
        expected_base_balance=100.3,
        expected_quote_balance=999422.77401,
        vol_of_unfilled_remaining_max_price=257.42,
    ),
    sell_partial_fill=SellPartialFillExpectation(
        order_price=257.42,
        n_open_orders=5,
        expected_sell_price=262.6,
        expected_sell_volume=0.38065504,
    ),
)

# Test data mapping for GridSell unfilled surplus strategy
GRIDSELL_UNFILLED_SURPLUS_TEST_DATA = {
    "XBTUSD": GRIDSELL_UNFILLED_SURPLUS_XBTUSD_EXPECTATIONS,
    "AAPLxUSD": GRIDSELL_UNFILLED_SURPLUS_AAPLXUSD_EXPECTATIONS,
}
