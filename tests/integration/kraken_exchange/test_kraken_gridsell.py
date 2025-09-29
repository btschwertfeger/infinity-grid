# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Integration tests for the GridSell strategy on Kraken exchange."""

import logging
from collections.abc import Callable
from decimal import Decimal
from unittest import mock

import pytest

from .helper import KrakenTestManager

LOG = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_sell.sleep", return_value=None)
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
                        59_999.9,
                    ),
                    "new_volumes": (
                        0.00170016,
                        0.00171717,
                        0.00173434,
                        0.00175168,
                        0.00168333,
                    ),
                    "new_sides": ("buy", "buy", "buy", "buy", "sell"),
                },
                "4_trigger_ensure_n_open_buy_orders": {
                    "new_price": 59_100.0,
                    "prices": (
                        58_817.7,
                        58_235.3,
                        57_658.7,
                        57_087.8,
                        59_999.9,
                        56_522.5,
                    ),
                    "volumes": (
                        0.00170016,
                        0.00171717,
                        0.00173434,
                        0.00175168,
                        0.00168333,
                        0.0017692,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "sell", "buy"),
                },
                "5_trigger_fill_sell_order": {
                    "new_price": 60_000.0,
                    "prices": (
                        58_817.7,
                        58_235.3,
                        57_658.7,
                        57_087.8,
                        56_522.5,
                    ),
                    "volumes": (
                        0.00170016,
                        0.00171717,
                        0.00173434,
                        0.00175168,
                        0.0017692,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy"),
                },
                "6_trigger_rapid_price_drop": {
                    "new_price": 50_000.0,
                    "prices": (
                        59_405.8,
                        58_817.6,
                        58_235.2,
                        57_658.6,
                        57_087.7,
                    ),
                    "volumes": (
                        0.00170016,
                        0.00171717,
                        0.00173434,
                        0.00175168,
                        0.0017692,
                    ),
                    "sides": ("sell", "sell", "sell", "sell", "sell"),
                },
                "7_trigger_all_sell_orders": {
                    "new_price": 59_100.0,
                    "buy_prices": (
                        58_514.8,
                        57_935.4,
                        57_361.7,
                        56_793.7,
                        56_231.3,
                    ),
                    "sell_prices": (59_405.8,),
                    "buy_volumes": (
                        0.00170896,
                        0.00172606,
                        0.00174332,
                        0.00176075,
                        0.00177836,
                    ),
                    "sell_volumes": (0.00170016,),
                },
                "8_check_max_investment_reached": {
                    "current_price": 50_000.0,
                    "n_open_sell_orders": 1,
                    "max_investment": 102.0,
                },
                "9_trigger_ensure_n_open_buy_orders": {
                    "new_price": 50_000.0,
                    "prices": (
                        59_405.8,
                        49_504.9,
                        49_014.7,
                        48_529.4,
                        48_048.9,
                        47_573.1,
                    ),
                    "volumes": (
                        0.00170016,
                        0.00202,
                        0.0020402,
                        0.0020606,
                        0.00208121,
                        0.00210202,
                    ),
                    "sides": ("sell", "buy", "buy", "buy", "buy", "buy"),
                },
                "10_check_not_enough_funds_for_sell": {
                    "sell_price": 49_504.8,
                    "n_orders": 6,
                    "n_sell_orders": 1,
                    "assume_base_available": 0.0,
                    "assume_quote_available": 1000.0,
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
                    "new_prices": (274.47, 271.75, 269.05, 266.38, 279.99),
                    "new_volumes": (
                        0.36433854,
                        0.36798528,
                        0.37167812,
                        0.37540355,
                        0.36072433,
                    ),
                    "new_sides": ("buy", "buy", "buy", "buy", "sell"),
                },
                "4_trigger_ensure_n_open_buy_orders": {
                    "new_price": 277.1,
                    "prices": (274.47, 271.75, 269.05, 266.38, 279.99, 263.74),
                    "volumes": (
                        0.36433854,
                        0.36798528,
                        0.37167812,
                        0.37540355,
                        0.36072433,
                        0.37916129,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "sell", "buy"),
                },
                "5_trigger_fill_sell_order": {
                    "new_price": 280.0,
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
                "6_trigger_rapid_price_drop": {
                    "new_price": 260.0,
                    "prices": (277.21, 274.46, 271.74, 269.04, 266.37),
                    "volumes": (
                        0.36433854,
                        0.36798528,
                        0.37167812,
                        0.37540355,
                        0.37916129,
                    ),
                    "sides": ("sell", "sell", "sell", "sell", "sell"),
                },
                "7_trigger_all_sell_orders": {  # FIXME: it is not selling all
                    "new_price": 275.0,
                    "buy_prices": (
                        272.27,
                        269.57,
                        266.9,
                        264.25,
                        261.63,
                    ),
                    "sell_prices": (277.21,),
                    "buy_volumes": (
                        0.36728247,
                        0.37096116,
                        0.37467216,
                        0.37842951,
                        0.38221916,
                    ),
                    "sell_volumes": (0.36433854,),
                },
                "8_check_max_investment_reached": {
                    "current_price": 270.0,
                    "n_open_sell_orders": 1,
                    "max_investment": 102.0,
                },
                "9_trigger_ensure_n_open_buy_orders": {
                    "new_price": 270.0,
                    "prices": (
                        277.21,
                        267.32,
                        264.67,
                        262.04,
                        259.44,
                        256.87,
                    ),
                    "volumes": (
                        0.36433854,
                        0.37408349,
                        0.37782899,
                        0.38162112,
                        0.38544557,
                        0.38930198,
                    ),
                    "sides": ("sell", "buy", "buy", "buy", "buy", "buy"),
                },
                "10_check_not_enough_funds_for_sell": {
                    "sell_price": 277.21,
                    "n_orders": 6,
                    "n_sell_orders": 1,
                    "assume_base_available": 0.0,
                    "assume_quote_available": 1000.0,
                },
            },
        ),
    ],
    ids=("BTCUSD", "AAPLxUSD"),
)
async def test_kraken_grid_sell(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    mock_sleep3: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    kraken_test_manager_factory: Callable[[str, str], KrakenTestManager],
    symbol: str,
    expectations: dict,
) -> None:
    """
    Integration test for the GridSell strategy using pre-generated websocket
    messages.

    This test simulates the full trading process of the trading algorithm, by
    leveraging a mocked Kraken API in order to verify interactions between the
    API, the algorithm and database. The test tries to cover almost all cases
    that could happen during the trading process.

    It tests:

    * Handling of ticker updates
    * Handling of execution updates
    * Initialization after the ticker and execution channels are connected
    * Placing of buy orders and shifting them up
    * Execution of buy orders and placement of corresponding sell orders
    * Execution of sell orders
    * Full database interactions using SQLite

    It does not cover the following cases:

    * Interactions related to telegram notifications
    * Initialization of the algorithm
    * Command-line interface / user-like interactions

    This one contains a lot of copy-paste, but hopefully doesn't need to get
    touched anymore.
    """
    LOG.info("******* Starting GridSell integration test *******")
    caplog.set_level(logging.INFO)

    tm = kraken_test_manager_factory(symbol, strategy="GridSell")
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
    # 5. FILLING A SELL ORDER
    await tm.trigger_fill_sell_order(
        new_price=expectations["5_trigger_fill_sell_order"]["new_price"],
        prices=expectations["5_trigger_fill_sell_order"]["prices"],
        volumes=expectations["5_trigger_fill_sell_order"]["volumes"],
        sides=expectations["5_trigger_fill_sell_order"]["sides"],
    )

    # ... as we can see, the sell order got removed from the orderbook.
    # ... there is no new corresponding buy order placed - this would only be
    # the case for the case, if there would be more sell orders.
    # As usual, if the price would rise higher, the buy orders would shift up.

    # ==========================================================================
    # 6. RAPID PRICE DROP - FILLING ALL BUY ORDERS
    await tm.trigger_rapid_price_drop(
        new_price=expectations["6_trigger_rapid_price_drop"]["new_price"],
        prices=expectations["6_trigger_rapid_price_drop"]["prices"],
        volumes=expectations["6_trigger_rapid_price_drop"]["volumes"],
        sides=expectations["6_trigger_rapid_price_drop"]["sides"],
    )
    # ==========================================================================
    # 7. SELL ALL AND ENSURE N OPEN BUY ORDERS
    await tm.trigger_all_sell_orders(
        new_price=expectations["7_trigger_all_sell_orders"]["new_price"],
        buy_prices=expectations["7_trigger_all_sell_orders"]["buy_prices"],
        sell_prices=expectations["7_trigger_all_sell_orders"]["sell_prices"],
        buy_volumes=expectations["7_trigger_all_sell_orders"]["buy_volumes"],
        sell_volumes=expectations["7_trigger_all_sell_orders"]["sell_volumes"],
    )

    # ==========================================================================
    # 8. MAX INVESTMENT REACHED
    await tm.check_max_investment_reached(
        current_price=expectations["8_check_max_investment_reached"]["current_price"],
        n_open_sell_orders=expectations["8_check_max_investment_reached"][
            "n_open_sell_orders"
        ],
        max_investment=expectations["8_check_max_investment_reached"]["max_investment"],
    )
    # After this, we need to retrigger the placement of n buy orders, otherwise
    # the following tests will fail.
    await tm.trigger_ensure_n_open_buy_orders(
        new_price=expectations["9_trigger_ensure_n_open_buy_orders"]["new_price"],
        prices=expectations["9_trigger_ensure_n_open_buy_orders"]["prices"],
        volumes=expectations["9_trigger_ensure_n_open_buy_orders"]["volumes"],
        sides=expectations["9_trigger_ensure_n_open_buy_orders"]["sides"],
    )

    # ==========================================================================
    # 9. Test what happens if there are not enough funds to place a sell order
    #    for some reason. The GridSell strategy will fail in this case to trigger
    #    a restart (handled by external process manager)
    # Ensure buy orders exist
    await tm.check_not_enough_funds_for_sell(
        sell_price=expectations["10_check_not_enough_funds_for_sell"]["sell_price"],
        n_orders=expectations["10_check_not_enough_funds_for_sell"]["n_orders"],
        n_sell_orders=expectations["10_check_not_enough_funds_for_sell"][
            "n_sell_orders"
        ],
        assume_base_available=expectations["10_check_not_enough_funds_for_sell"][
            "assume_base_available"
        ],
        assume_quote_available=expectations["10_check_not_enough_funds_for_sell"][
            "assume_quote_available"
        ],
        fail=True,
    )


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_sell.sleep", return_value=None)
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
                "2_partly_filled_pt1": {
                    "fill_volume": 0.002,
                    "n_open_orders": 5,
                    "expected_base_balance": Decimal("100.002"),
                    "expected_quote_balance": 999_400.99,
                    "vol_of_unfilled_remaining_max_price": 49_504.9,
                },
                "3_partly_filled_pt2": {
                    "order_price": 49_504.9,
                    "n_open_orders": 5,
                    "expected_sell_price": 50_500.0,
                    "expected_sell_volume": 0.00199014,
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
                "2_partly_filled_pt1": {
                    "fill_volume": 0.3,
                    "n_open_orders": 5,
                    "expected_base_balance": Decimal("100.3"),
                    "expected_quote_balance": 999422.77401,
                    "vol_of_unfilled_remaining_max_price": 257.42,
                },
                "3_partly_filled_pt2": {
                    "order_price": 257.42,
                    "n_open_orders": 5,
                    "expected_sell_price": 262.6,
                    "expected_sell_volume": 0.38065504,
                },
            },
        ),
    ],
    ids=("BTCUSD", "AAPLxUSD"),
)
async def test_kraken_grid_sell_unfilled_surplus(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.Mock,  # noqa: ARG001
    mock_sleep3: mock.Mock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    kraken_test_manager_factory: Callable[[str, str], KrakenTestManager],
    symbol: str,
    expectations: dict,
) -> None:
    """
    Integration test for the GridSell strategy using pre-generated websocket
    messages.

    This test checks if the unfilled surplus is handled correctly.

    unfilled surplus: The base currency volume that was partly filled by an buy
    order, before the order was cancelled.
    """
    LOG.info("******* Starting GridSell unfilled surplus integration test *******")
    caplog.set_level(logging.INFO)

    tm = kraken_test_manager_factory(symbol, strategy="GridSell")
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
    # 2. BUYING PARTLY FILLED and ensure that the unfilled surplus is handled
    LOG.info("******* Check partially filled orders *******")

    api = tm.ws_client.__websocket_service
    api.fill_order(
        tm.strategy._orderbook_table.get_orders().first().txid,
        expectations["2_partly_filled_pt1"]["fill_volume"],
    )
    assert tm.strategy._orderbook_table.count() == 5

    balances = api.get_balances()
    assert (
        Decimal(balances[tm.exchange_config.base_currency]["balance"])
        == expectations["2_partly_filled_pt1"]["expected_base_balance"]
    )
    assert float(
        balances[tm.exchange_config.quote_currency]["balance"],
    ) == pytest.approx(expectations["2_partly_filled_pt1"]["expected_quote_balance"])

    tm.strategy._handle_cancel_order(
        tm.strategy._orderbook_table.get_orders().first().txid,
    )

    assert (
        tm.strategy._configuration_table.get()["vol_of_unfilled_remaining"]
        == expectations["2_partly_filled_pt1"]["fill_volume"]
    )
    assert (
        tm.strategy._configuration_table.get()["vol_of_unfilled_remaining_max_price"]
        == expectations["2_partly_filled_pt1"]["vol_of_unfilled_remaining_max_price"]
    )

    # ==========================================================================
    # 3. SELLING THE UNFILLED SURPLUS
    #    The sell-check is done only during cancelling orders, as this is the
    #    only time where this amount is touched. So we need to create another
    #    partly filled order.
    LOG.info("******* Check selling the unfilled surplus *******")

    tm.strategy.new_buy_order(
        order_price=expectations["3_partly_filled_pt2"]["order_price"],
    )
    assert tm.strategy._orderbook_table.count() == 5
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
        == expectations["3_partly_filled_pt2"]["n_open_orders"]
    )

    order = tm.strategy._orderbook_table.get_orders(
        filters={"price": expectations["3_partly_filled_pt2"]["order_price"]},
    ).all()[0]
    api.fill_order(order["txid"], expectations["2_partly_filled_pt1"]["fill_volume"])
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
        == expectations["3_partly_filled_pt2"]["n_open_orders"]
    )
    assert (
        tm.strategy._configuration_table.get()["vol_of_unfilled_remaining_max_price"]
        == 0.0
    )

    sell_orders = tm.strategy._orderbook_table.get_orders(
        filters={"side": "sell"},
    ).all()
    assert (
        sell_orders[0].price
        == expectations["3_partly_filled_pt2"]["expected_sell_price"]
    )
    assert sell_orders[0].volume == pytest.approx(
        expectations["3_partly_filled_pt2"]["expected_sell_volume"],
    )
