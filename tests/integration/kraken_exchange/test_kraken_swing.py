# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Integration tests for the SWING strategy on Kraken exchange."""

import logging
from collections.abc import Callable
from decimal import Decimal
from unittest import mock

import pytest

from .kraken_test_manager import KrakenIntegrationTestManager

LOG = logging.getLogger(__name__)


@pytest.mark.wip
@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.swing.sleep", return_value=None)
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
                        51_005.0,
                    ),
                    "volumes": (
                        0.00202,
                        0.0020402,
                        0.0020606,
                        0.00208121,
                        0.00210202,
                        0.00197044,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy", "sell"),
                },
                "2_trigger_rapid_price_drop": {
                    "new_price": 40_000.0,
                    "prices": (
                        51_005.0,
                        49_999.9,
                        49_504.8,
                        49_014.6,
                        48_529.3,
                        48_048.8,
                    ),
                    "volumes": (
                        0.00197044,
                        0.00201005,
                        0.00203015,
                        0.00205046,
                        0.00207096,
                        0.00209167,
                    ),
                    "sides": ("sell", "sell", "sell", "sell", "sell", "sell"),
                },
                "3_trigger_ensure_n_open_buy_orders": {
                    "new_price": 40_000.1,
                    "prices": (
                        51_005.0,
                        49_999.9,
                        49_504.8,
                        49_014.6,
                        48_529.3,
                        48_048.8,
                        39_604.0,
                        39_211.8,
                        38_823.5,
                        38_439.1,
                        38_058.5,
                    ),
                    "volumes": (
                        0.00197044,
                        0.00201005,
                        0.00203015,
                        0.00205046,
                        0.00207096,
                        0.00209167,
                        0.00252499,
                        0.00255025,
                        0.00257575,
                        0.00260151,
                        0.00262753,
                    ),
                    "sides": (
                        "sell",
                        "sell",
                        "sell",
                        "sell",
                        "sell",
                        "sell",
                        "buy",
                        "buy",
                        "buy",
                        "buy",
                        "buy",
                    ),
                },
                "4_trigger_shift_up_buy_orders": {
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
                "5_check_not_enough_funds_for_sell": {
                    "sell_price": 59_000.0,
                    "n_orders": 4,
                    "n_sell_orders": 0,
                    "assume_base_available": 0.0,
                    "assume_quote_available": 1_000.0,
                },
            },
        ),
        (
            "AAPLxUSD",
            {
                "initial_ticker": 260.0,
                "1_check_initial_n_buy_orders": {
                    "prices": (
                        257.42,
                        254.87,
                        252.34,
                        249.84,
                        247.36,
                        265.22,
                    ),
                    "volumes": (
                        0.3884702,
                        0.39235688,
                        0.39629071,
                        0.40025616,
                        0.40426908,
                        0.37689471,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy", "sell"),
                },
                "2_trigger_rapid_price_drop": {
                    # Lets fill some of the buy orders, but not all.
                    "new_price": 250.0,
                    "prices": (
                        249.84,
                        247.36,
                        265.22,
                        259.99,
                        257.41,
                        254.86,
                    ),
                    "volumes": (
                        0.40025616,
                        0.40426908,
                        0.37689471,
                        0.38447638,
                        0.38832996,
                        0.39221539,
                    ),
                    "sides": ("buy", "buy", "sell", "sell", "sell", "sell"),
                },
                "3_trigger_ensure_n_open_buy_orders": {
                    "new_price": 250.1,
                    "prices": (
                        249.84,
                        247.36,
                        265.22,
                        259.99,
                        257.41,
                        254.86,
                        244.91,
                        242.48,
                        240.07,
                    ),
                    "volumes": (
                        0.40025616,
                        0.40426908,
                        0.37689471,
                        0.38447638,
                        0.38832996,
                        0.39221539,
                        0.40831325,
                        0.41240514,
                        0.41654517,
                    ),
                    "sides": (
                        "buy",
                        "buy",
                        "sell",
                        "sell",
                        "sell",
                        "sell",
                        "buy",
                        "buy",
                        "buy",
                    ),
                },
                "4_trigger_shift_up_buy_orders": {
                    "new_price": 255.0,
                    "prices": (
                        249.84,
                        247.36,
                        265.22,
                        259.99,
                        257.41,
                        244.91,
                        242.48,
                        240.07,
                    ),
                    "volumes": (
                        0.40025616,
                        0.40426908,
                        0.37689471,
                        0.38447638,
                        0.38832996,
                        0.40831325,
                        0.41240514,
                        0.41654517,
                    ),
                    "sides": (
                        "buy",
                        "buy",
                        "sell",
                        "sell",
                        "sell",
                        "buy",
                        "buy",
                        "buy",
                    ),
                },
                "5_check_not_enough_funds_for_sell": {
                    "sell_price": 257.41,
                    "n_orders": 7,
                    "n_sell_orders": 2,
                    "assume_base_available": 0.0,
                    "assume_quote_available": 1_000.0,
                },
            },
        ),
    ],
    ids=("BTCUSD", "AAPLxUSD"),
)
async def test_kraken_swing(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    mock_sleep3: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable[[str, str], KrakenIntegrationTestManager],
    symbol: str,
    expectations: dict,
) -> None:
    """
    Integration test for the SWING strategy using pre-generated websocket
    messages.
    """
    LOG.info("******* Starting SWING integration test *******")
    caplog.set_level(logging.INFO)

    tm = test_manager_factory("Kraken", symbol, strategy="SWING")
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
    # 2. RAPID PRICE DROP - FILLING ALL BUY ORDERS + CREATING SELL ORDERS
    # Now check the behavior for a rapid price drop.
    # It should fill the buy orders and place 6 new sell orders.
    await tm.trigger_rapid_price_drop(
        new_price=expectations["2_trigger_rapid_price_drop"]["new_price"],
        prices=expectations["2_trigger_rapid_price_drop"]["prices"],
        volumes=expectations["2_trigger_rapid_price_drop"]["volumes"],
        sides=expectations["2_trigger_rapid_price_drop"]["sides"],
    )

    # ==========================================================================
    # 3. NEW TICKER TO ENSURE N OPEN BUY ORDERS
    await tm.trigger_ensure_n_open_buy_orders(
        new_price=expectations["3_trigger_ensure_n_open_buy_orders"]["new_price"],
        prices=expectations["3_trigger_ensure_n_open_buy_orders"]["prices"],
        volumes=expectations["3_trigger_ensure_n_open_buy_orders"]["volumes"],
        sides=expectations["3_trigger_ensure_n_open_buy_orders"]["sides"],
    )

    # ==========================================================================
    # 4. FILLING SELL ORDERS WHILE SHIFTING UP BUY ORDERS
    # Check if shifting up the buy orders works
    api = tm.ws_client.__websocket_service

    base_balance_before = float(
        api.get_balances()[tm.exchange_config.base_currency]["balance"],
    )
    quote_balance_before = float(
        api.get_balances()[tm.exchange_config.quote_currency]["balance"],
    )

    await tm.trigger_shift_up_buy_orders(
        new_price=expectations["4_trigger_shift_up_buy_orders"]["new_price"],
        prices=expectations["4_trigger_shift_up_buy_orders"]["prices"],
        volumes=expectations["4_trigger_shift_up_buy_orders"]["volumes"],
        sides=expectations["4_trigger_shift_up_buy_orders"]["sides"],
    )

    # Ensure that profit has been made
    assert (
        float(api.get_balances()[tm.exchange_config.base_currency]["balance"])
        < base_balance_before
    )
    assert (
        float(api.get_balances()[tm.exchange_config.quote_currency]["balance"])
        > quote_balance_before
    )

    # ==========================================================================
    # 5. Test what happens if there are not enough funds to place a sell order
    #    for some reason.
    await tm.check_not_enough_funds_for_sell(
        sell_price=expectations["5_check_not_enough_funds_for_sell"]["sell_price"],
        n_orders=expectations["5_check_not_enough_funds_for_sell"]["n_orders"],
        n_sell_orders=expectations["5_check_not_enough_funds_for_sell"][
            "n_sell_orders"
        ],
        assume_base_available=expectations["5_check_not_enough_funds_for_sell"][
            "assume_base_available"
        ],
        assume_quote_available=expectations["5_check_not_enough_funds_for_sell"][
            "assume_quote_available"
        ],
        fail=False,
    )


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.swing.sleep", return_value=None)
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
                        51_005.0,
                    ),
                    "volumes": (
                        0.00202,
                        0.0020402,
                        0.0020606,
                        0.00208121,
                        0.00210202,
                        0.00197044,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy", "sell"),
                },
                "2_balance_approximately": {
                    "base_balance": 99.99802956,
                    "base_hold": 0.00197044,
                    "quote_balance": 999_500.0011705891,
                    "quote_hold": 499.99882941100003,
                },
                "3_partly_filled_pt1": {
                    "fill_volume": 0.002,
                    "n_open_orders": 6,
                    "expected_base_balance": Decimal("100.002"),
                    "expected_quote_balance": 999_400.99,
                    "vol_of_unfilled_remaining_max_price": 49_504.9,
                    "approximations": {
                        "base_balance": 100.00002956,
                        "base_hold": 0.00197044,
                        "quote_balance": 999_400.9913705891,
                        "quote_hold": 400.98902941100005,
                    },
                },
                "4_partly_filled_pt2": {
                    "order_price": 49_504.9,
                    "n_open_orders": 6,
                    "expected_sell_price": 50_500.0,
                    "expected_sell_volume": 0.00199014,
                },
                "5_check_max_investment_reached": {
                    "current_price": 50_000.0,
                    "n_open_sell_orders": 2,
                },
            },
        ),
        (
            "AAPLxUSD",
            {
                "initial_ticker": 260.0,
                "1_check_initial_n_buy_orders": {
                    "prices": (
                        257.42,
                        254.87,
                        252.34,
                        249.84,
                        247.36,
                        265.22,
                    ),
                    "volumes": (
                        0.3884702,
                        0.39235688,
                        0.39629071,
                        0.40025616,
                        0.40426908,
                        0.37689471,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy", "sell"),
                },
                "2_balance_approximately": {
                    "base_balance": 99.62310529,
                    "base_hold": 0.37689471,
                    "quote_balance": 999_500.0011705891,
                    "quote_hold": 499.99999,
                },
                "3_partly_filled_pt1": {
                    "fill_volume": 0.3,
                    "n_open_orders": 6,
                    "expected_base_balance": Decimal("100.3"),
                    "expected_quote_balance": 999_422.77401,
                    "vol_of_unfilled_remaining_max_price": 257.42,
                    "approximations": {
                        "base_balance": 99.92310529,
                        "base_hold": 0.37689471,
                        "quote_balance": 999_422.77401,
                        "quote_hold": 422.77399,
                    },
                },
                "4_partly_filled_pt2": {
                    "order_price": 257.42,
                    "n_open_orders": 6,
                    "expected_sell_price": 262.6,
                    "expected_sell_volume": 0.38065504,
                },
                "5_check_max_investment_reached": {
                    "current_price": 257.42,
                    "n_open_sell_orders": 2,
                },
            },
        ),
    ],
    ids=("BTCUSD", "AAPLxUSD"),
)
async def test_kraken_swing_unfilled_surplus(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.Mock,  # noqa: ARG001
    mock_sleep3: mock.Mock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable[[str, str], KrakenIntegrationTestManager],
    symbol: str,
    expectations: dict,
) -> None:
    """
    Integration test for the SWING strategy using pre-generated websocket
    messages.

    This test checks if the unfilled surplus is handled correctly.

    unfilled surplus: The base currency volume that was partly filled by an buy
    order, before the order was cancelled.
    """
    LOG.info("******* Starting SWING unfilled surplus integration test *******")
    caplog.set_level(logging.INFO)

    tm = test_manager_factory("Kraken", symbol, strategy="SWING")
    await tm.initialize_engine()
    await tm.trigger_prepare_for_trading(initial_ticker=expectations["initial_ticker"])

    # ==========================================================================
    # 1. PLACEMENT OF INITIAL N BUY ORDERS
    await tm.check_initial_n_buy_orders(
        prices=expectations["1_check_initial_n_buy_orders"]["prices"],
        volumes=expectations["1_check_initial_n_buy_orders"]["volumes"],
        sides=expectations["1_check_initial_n_buy_orders"]["sides"],
    )
    api = tm.ws_client.__websocket_service

    balances = api.get_balances()
    assert float(
        balances[tm.exchange_config.base_currency]["balance"],
    ) == pytest.approx(expectations["2_balance_approximately"]["base_balance"])
    assert float(
        balances[tm.exchange_config.base_currency]["hold_trade"],
    ) == pytest.approx(expectations["2_balance_approximately"]["base_hold"])
    assert float(
        balances[tm.exchange_config.quote_currency]["balance"],
    ) == pytest.approx(expectations["2_balance_approximately"]["quote_balance"])
    assert float(
        balances[tm.exchange_config.quote_currency]["hold_trade"],
    ) == pytest.approx(expectations["2_balance_approximately"]["quote_hold"])

    # ==========================================================================
    # 2. BUYING PARTLY FILLED and ensure that the unfilled surplus is handled
    # correctly.
    LOG.info("******* Check handling of unfilled surplus *******")
    api.fill_order(
        tm.strategy._orderbook_table.get_orders().first().txid,
        expectations["3_partly_filled_pt1"]["fill_volume"],
    )
    assert (
        tm.strategy._orderbook_table.count()
        == expectations["3_partly_filled_pt1"]["n_open_orders"]
    )

    # We have not 100.002 here, since the Swing is initially creating a sell
    # order which reduces the available base balance.
    balances = api.get_balances()
    assert float(
        balances[tm.exchange_config.base_currency]["balance"],
    ) == pytest.approx(
        expectations["3_partly_filled_pt1"]["approximations"]["base_balance"],
    )
    assert float(
        balances[tm.exchange_config.base_currency]["hold_trade"],
    ) == pytest.approx(
        expectations["3_partly_filled_pt1"]["approximations"]["base_hold"],
    )
    assert float(
        balances[tm.exchange_config.quote_currency]["balance"],
    ) == pytest.approx(
        expectations["3_partly_filled_pt1"]["approximations"]["quote_balance"],
    )
    assert float(
        balances[tm.exchange_config.quote_currency]["hold_trade"],
    ) == pytest.approx(
        expectations["3_partly_filled_pt1"]["approximations"]["quote_hold"],
    )

    tm.strategy._handle_cancel_order(
        tm.strategy._orderbook_table.get_orders().first().txid,
    )

    assert (
        tm.strategy._configuration_table.get()["vol_of_unfilled_remaining"]
        == expectations["3_partly_filled_pt1"]["fill_volume"]
    )
    assert (
        tm.strategy._configuration_table.get()["vol_of_unfilled_remaining_max_price"]
        == expectations["3_partly_filled_pt1"]["vol_of_unfilled_remaining_max_price"]
    )

    # ==========================================================================
    # 3. SELLING THE UNFILLED SURPLUS
    #    The sell-check is done only during cancelling orders, as this is the
    #    only time where this amount is touched. So we need to create another
    #    partly filled order.
    LOG.info("******* Check selling the unfilled surplus *******")
    tm.strategy.new_buy_order(
        order_price=expectations["4_partly_filled_pt2"]["order_price"],
    )
    assert (
        tm.strategy._orderbook_table.count()
        == expectations["4_partly_filled_pt2"]["n_open_orders"]
    )
    assert (
        len(
            [
                o
                for o in tm.rest_api.get_open_orders(
                    userref=tm.strategy._config.userref,
                )
                if o.status == "open"
            ],
        )
        == expectations["4_partly_filled_pt2"]["n_open_orders"]
    )

    order = tm.strategy._orderbook_table.get_orders(
        filters={"price": expectations["4_partly_filled_pt2"]["order_price"]},
    ).all()[0]
    api.fill_order(order["txid"], expectations["3_partly_filled_pt1"]["fill_volume"])
    tm.strategy._handle_cancel_order(order["txid"])

    assert (
        len(
            [
                o
                for o in tm.rest_api.get_open_orders(
                    userref=tm.strategy._config.userref,
                )
                if o.status == "open"
            ],
        )
        == expectations["4_partly_filled_pt2"]["n_open_orders"]
    )
    assert (
        tm.strategy._configuration_table.get()["vol_of_unfilled_remaining_max_price"]
        == 0.0
    )

    sell_orders = tm.strategy._orderbook_table.get_orders(
        filters={"side": "sell", "id": 7},
    ).all()
    assert (
        sell_orders[0].price
        == expectations["4_partly_filled_pt2"]["expected_sell_price"]
    )
    assert sell_orders[0].volume == pytest.approx(
        expectations["4_partly_filled_pt2"]["expected_sell_volume"],
    )

    # ==========================================================================
    # 4. MAX INVESTMENT REACHED
    await tm.check_max_investment_reached(
        current_price=expectations["5_check_max_investment_reached"]["current_price"],
        n_open_sell_orders=expectations["5_check_max_investment_reached"][
            "n_open_sell_orders"
        ],
    )
