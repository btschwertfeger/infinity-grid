# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Integration tests for cDCA strategy on Kraken exchange."""

import logging
from typing import Callable
from unittest import mock

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("symbol", "expectations"),
    [
        (
            "XBTUSD",
            {
                "initial_ticker": 50_000.0,
                "1_check_initial_n_buy_orders": {
                    "prices": (
                        49_504.9,
                        49_014.7,
                        48_529.4,
                        48_048.9,
                        47_573.1,
                    ),
                    "volumes": (
                        0.00202,
                        0.0020402,
                        0.0020606,
                        0.00208121,
                        0.00210202,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy"),
                },
                "2_trigger_shift_up_buy_orders": {
                    "new_price": 60_000.0,
                    "prices": (
                        59_405.9,
                        58_817.7,
                        58_235.3,
                        57_658.7,
                        57_087.8,
                    ),
                    "volumes": (
                        0.00168333,
                        0.00170016,
                        0.00171717,
                        0.00173434,
                        0.00175168,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy"),
                },
                "3_trigger_fill_buy_order": {
                    "no_trigger_price": 59_990.0,
                    "new_price": 59_000.0,
                    "old_prices": (
                        59_405.9,
                        58_817.7,
                        58_235.3,
                        57_658.7,
                        57_087.8,
                    ),
                    "old_volumes": (
                        0.00168333,
                        0.00170016,
                        0.00171717,
                        0.00173434,
                        0.00175168,
                    ),
                    "old_sides": ("buy", "buy", "buy", "buy", "buy"),
                    "new_prices": (
                        58_817.7,
                        58_235.3,
                        57_658.7,
                        57_087.8,
                    ),
                    "new_volumes": (
                        0.00170016,
                        0.00171717,
                        0.00173434,
                        0.00175168,
                    ),
                    "new_sides": ("buy", "buy", "buy", "buy"),
                },
                "4_trigger_ensure_n_open_buy_orders": {
                    "new_price": 59_100.0,
                    "prices": (58_817.7, 58_235.3, 57_658.7, 57_087.8, 56_522.5),
                    "volumes": (
                        0.00170016,
                        0.00171717,
                        0.00173434,
                        0.00175168,
                        0.0017692,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy"),
                },
                "5_trigger_rapid_price_drop": {
                    "new_price": 50_000.0,
                    "prices": (),
                    "volumes": (),
                    "sides": (),
                },
                "6_trigger_ensure_n_open_buy_orders": {
                    "new_price": 50_100.0,
                    "prices": (
                        49_603.9,
                        49_112.7,
                        48_626.4,
                        48_144.9,
                        47_668.2,
                    ),
                    "volumes": (
                        0.00201597,
                        0.00203613,
                        0.00205649,
                        0.00207706,
                        0.00209783,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy"),
                },
                "7_check_max_investment_reached": {
                    "current_price": 50_000.0,
                    "n_open_sell_orders": 0,
                    "max_investment": 50.0,
                },
            },
        ),
        (
            "AAPLxUSD",
            {
                "initial_ticker": 260.0,
                "1_check_initial_n_buy_orders": {
                    "prices": (257.42, 254.87, 252.34, 249.84, 247.36),
                    "volumes": (
                        0.3884702,
                        0.39235688,
                        0.39629071,
                        0.40025616,
                        0.40426908,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy"),
                },
                "2_trigger_shift_up_buy_orders": {
                    "new_price": 280.0,
                    "prices": (277.22, 274.47, 271.75, 269.05, 266.38),
                    "volumes": (
                        0.36072433,
                        0.36433854,
                        0.36798528,
                        0.37167812,
                        0.37540355,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy"),
                },
                "3_trigger_fill_buy_order": {
                    "no_trigger_price": 279.0,
                    "new_price": 277.0,
                    "old_prices": (277.22, 274.47, 271.75, 269.05, 266.38),
                    "old_volumes": (
                        0.36072433,
                        0.36433854,
                        0.36798528,
                        0.37167812,
                        0.37540355,
                    ),
                    "old_sides": ("buy", "buy", "buy", "buy", "buy"),
                    "new_prices": (274.47, 271.75, 269.05, 266.38),
                    "new_volumes": (
                        0.36433854,
                        0.36798528,
                        0.37167812,
                        0.37540355,
                    ),
                    "new_sides": ("buy", "buy", "buy", "buy"),
                },
                "4_trigger_ensure_n_open_buy_orders": {
                    "new_price": 277.1,
                    "prices": (274.47, 271.75, 269.05, 266.38, 263.74),
                    "volumes": (
                        0.36433854,
                        0.36798528,
                        0.37167812,
                        0.37540355,
                        0.37916129,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy"),
                },
                "5_trigger_rapid_price_drop": {
                    "new_price": 260.0,
                    "prices": (),
                    "volumes": (),
                    "sides": (),
                },
                "6_trigger_ensure_n_open_buy_orders": {
                    "new_price": 260.0,
                    "prices": (257.42, 254.87, 252.34, 249.84, 247.36),
                    "volumes": (
                        0.3884702,
                        0.39235688,
                        0.39629071,
                        0.40025616,
                        0.40426908,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy"),
                },
                "7_check_max_investment_reached": {
                    "current_price": 260.0,
                    "n_open_sell_orders": 0,
                    "max_investment": 50.0,
                },
            },
        ),
    ],
    ids=("BTCUSD", "AAPLxUSD"),
)
async def test_kraken_cdca(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable,
    symbol: str,
    expectations: dict,
) -> None:
    """
    Integration test for cDCA strategy using pre-generated websocket messages.
    """
    caplog.set_level(logging.INFO)

    tm = test_manager_factory("Kraken", symbol, strategy="cDCA")
    await tm.initialize_engine()
    await tm.trigger_prepare_for_trading(initial_ticker=expectations["initial_ticker"])

    # ==========================================================================
    # 1. PLACEMENT OF INITIAL N BUY ORDERS
    await tm.check_initial_n_buy_orders(
        prices=expectations["1_check_initial_n_buy_orders"]["prices"],
        volumes=expectations["1_check_initial_n_buy_orders"]["volumes"],
        sides=expectations["1_check_initial_n_buy_orders"]["sides"],
    )

    # ==========================================================================
    # 2. SHIFTING UP BUY ORDERS
    await tm.trigger_shift_up_buy_orders(
        new_price=expectations["2_trigger_shift_up_buy_orders"]["new_price"],
        prices=expectations["2_trigger_shift_up_buy_orders"]["prices"],
        volumes=expectations["2_trigger_shift_up_buy_orders"]["volumes"],
        sides=expectations["2_trigger_shift_up_buy_orders"]["sides"],
    )
    # ==========================================================================
    # 3. FILLING A BUY ORDER
    # Now lets let the price drop a bit so that a buy order gets triggered.
    await tm.trigger_fill_buy_order(
        no_trigger_price=expectations["3_trigger_fill_buy_order"]["no_trigger_price"],
        new_price=expectations["3_trigger_fill_buy_order"]["new_price"],
        old_prices=expectations["3_trigger_fill_buy_order"]["old_prices"],
        old_volumes=expectations["3_trigger_fill_buy_order"]["old_volumes"],
        old_sides=expectations["3_trigger_fill_buy_order"]["old_sides"],
        new_prices=expectations["3_trigger_fill_buy_order"]["new_prices"],
        new_volumes=expectations["3_trigger_fill_buy_order"]["new_volumes"],
        new_sides=expectations["3_trigger_fill_buy_order"]["new_sides"],
    )

    # ==========================================================================
    # 4. ENSURING N OPEN BUY ORDERS
    await tm.trigger_ensure_n_open_buy_orders(
        new_price=expectations["4_trigger_ensure_n_open_buy_orders"]["new_price"],
        prices=expectations["4_trigger_ensure_n_open_buy_orders"]["prices"],
        volumes=expectations["4_trigger_ensure_n_open_buy_orders"]["volumes"],
        sides=expectations["4_trigger_ensure_n_open_buy_orders"]["sides"],
    )

    # ==========================================================================
    # 5. RAPID PRICE DROP - FILLING ALL BUY ORDERS
    # Now check the behavior for a rapid price drop.
    await tm.trigger_rapid_price_drop(
        new_price=expectations["5_trigger_rapid_price_drop"]["new_price"],
        prices=expectations["5_trigger_rapid_price_drop"]["prices"],
        volumes=expectations["5_trigger_rapid_price_drop"]["volumes"],
        sides=expectations["5_trigger_rapid_price_drop"]["sides"],
    )

    # ==========================================================================
    # 6. ENSURE N OPEN BUY ORDERS ... after rapid price drop has filled all buy
    #    orders
    await tm.trigger_ensure_n_open_buy_orders(
        new_price=expectations["6_trigger_ensure_n_open_buy_orders"]["new_price"],
        prices=expectations["6_trigger_ensure_n_open_buy_orders"]["prices"],
        volumes=expectations["6_trigger_ensure_n_open_buy_orders"]["volumes"],
        sides=expectations["6_trigger_ensure_n_open_buy_orders"]["sides"],
    )

    # ==========================================================================
    # 7. MAX INVESTMENT REACHED
    await tm.check_max_investment_reached(
        current_price=expectations["7_check_max_investment_reached"]["current_price"],
        n_open_sell_orders=expectations["7_check_max_investment_reached"][
            "n_open_sell_orders"
        ],
        max_investment=expectations["7_check_max_investment_reached"]["max_investment"],
    )
