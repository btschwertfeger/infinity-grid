# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Integration tests for the GridHODL strategy on Kraken exchange.

FIXME: Add a check for removing buy orders that are placed to close to each
other.
"""

import logging
from decimal import Decimal
from unittest import mock

import pytest

from infinity_grid.models.configuration import (
    BotConfigDTO,
    DBConfigDTO,
    NotificationConfigDTO,
)

from .helper import KrakenTestManager
from .kraken_exchange_api import KrakenExchangeAPIConfig

LOG = logging.getLogger(__name__)


@pytest.fixture
def kraken_gridhodl_bot_config() -> BotConfigDTO:
    return BotConfigDTO(
        strategy="GridHODL",
        exchange="Kraken",
        api_public_key="",
        api_secret_key="",
        name="Local Tests Bot GridHODL",
        userref=0,
        base_currency="BTC",
        quote_currency="USD",
        max_investment=10_000.0,
        amount_per_grid=100.0,
        interval=0.01,
        n_open_buy_orders=5,
        verbosity=0,
    )


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_hodl.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("bot_config", "kraken_config", "expectations"),
    [
        (
            BotConfigDTO(
                strategy="GridHODL",
                exchange="Kraken",
                api_public_key="",
                api_secret_key="",
                name="Local Tests Bot GridHODL",
                userref=0,
                base_currency="BTC",
                quote_currency="USD",
                max_investment=10_000.0,
                amount_per_grid=100.0,
                interval=0.01,
                n_open_buy_orders=5,
                verbosity=0,
            ),
            KrakenExchangeAPIConfig(
                base_currency="XXBT",
                quote_currency="ZUSD",
                pair="XBTUSD",
                ws_symbol="BTC/USD",
            ),
            {
                "initial_ticker": 50_000.0,
                "check_initial_n_buy_orders": {
                    "prices": (49_504.9, 49_014.7, 48_529.4, 48_048.9, 47_573.1),
                    "volumes": (0.00202, 0.0020402, 0.0020606, 0.00208121, 0.00210202),
                    "sides": ("buy", "buy", "buy", "buy", "buy"),
                },
                "trigger_shift_up_buy_orders": {
                    "new_price": 60_000.0,
                    "prices": (59_405.9, 58_817.7, 58_235.3, 57_658.7, 57_087.8),
                    "volumes": (
                        0.00168333,
                        0.00170016,
                        0.00171717,
                        0.00173434,
                        0.00175168,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy"),
                },
                "trigger_fill_buy_order": {
                    "no_trigger_price": 59_990.0,
                    "new_price": 59_000.0,
                    "old_prices": (59_405.9, 58_817.7, 58_235.3, 57_658.7, 57_087.8),
                    "old_volumes": (
                        0.00168333,
                        0.00170016,
                        0.00171717,
                        0.00173434,
                        0.00175168,
                    ),
                    "old_sides": ("buy", "buy", "buy", "buy", "buy"),
                    "new_prices": (58_817.7, 58_235.3, 57_658.7, 57_087.8, 59_999.9),
                    "new_volumes": (
                        0.00170016,
                        0.00171717,
                        0.00173434,
                        0.00175168,
                        0.00167504,
                    ),
                    "new_sides": ("buy", "buy", "buy", "buy", "sell"),
                },
                "trigger_ensure_n_open_buy_orders": {
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
                        0.00167504,
                        0.0017692,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "sell", "buy"),
                },
                "trigger_fill_sell_order": {
                    "new_price": 60_000.0,
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
                "trigger_rapid_price_drop": {
                    "new_price": 50_000.0,
                    "prices": (59_405.8, 58_817.6, 58_235.2, 57_658.6, 57_087.7),
                    "volumes": (
                        0.00169179,
                        0.00170871,
                        0.0017258,
                        0.00174306,
                        0.00176049,
                    ),
                    "sides": ("sell", "sell", "sell", "sell", "sell"),
                },
                "trigger_all_sell_orders": {  # FIXME: this is not triggering all sell orders
                    "new_price": 59_100.0,
                    "buy_prices": (58_514.8, 57_935.4, 57_361.7, 56_793.7, 56_231.3),
                    "sell_prices": (59_405.8,),
                    "buy_volumes": (
                        0.00170896,
                        0.00172606,
                        0.00174332,
                        0.00176075,
                        0.00177836,
                    ),
                    "sell_volumes": (0.00169179,),
                },
                "check_not_enough_funds_for_sell": {
                    "sell_price": 58_500.0,
                    "n_orders": 5,
                    "n_sell_orders": 1,
                    "assume_base_available": 0.0,
                    "assume_quote_available": 1000.0,
                },
                "sell_after_not_enough_funds_for_sell": {
                    "price": 58_500.0,
                    "n_orders": 7,
                    "sell_prices": (59_405.8, 59_099.9),
                    "sell_volumes": (0.00169179, 0.00170055),
                },
                "check_max_investment_reached": {
                    "current_price": 50_000.0,
                    "n_open_sell_orders": 2,
                    "max_investment": 202.0,
                },
            },
        ),
        (
            BotConfigDTO(
                strategy="GridHODL",
                exchange="Kraken",
                api_public_key="",
                api_secret_key="",
                name="Local Tests Bot GridHODL",
                userref=0,
                base_currency="AAPLx",
                quote_currency="USD",
                max_investment=10_000.0,
                amount_per_grid=100.0,
                interval=0.01,
                n_open_buy_orders=5,
                verbosity=0,
            ),
            KrakenExchangeAPIConfig(
                base_currency="AAPLx",
                quote_currency="ZUSD",
                pair="AAPLxUSD",
                ws_symbol="AAPLx/USD",
            ),
            {
                "initial_ticker": 260.0,
                "check_initial_n_buy_orders": {
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
                "trigger_shift_up_buy_orders": {
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
                "trigger_fill_buy_order": {
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
                        0.3570128,
                    ),
                    "new_sides": ("buy", "buy", "buy", "buy", "sell"),
                },
                "trigger_ensure_n_open_buy_orders": {
                    "new_price": 277.1,
                    "prices": (
                        274.47,
                        271.75,
                        269.05,
                        266.38,
                        279.99,
                        263.74,
                    ),
                    "volumes": (
                        0.36433854,
                        0.36798528,
                        0.37167812,
                        0.37540355,
                        0.3570128,
                        0.37916129,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "sell", "buy"),
                },
                "trigger_fill_sell_order": {
                    "new_price": 280.0,
                    "prices": (
                        274.47,
                        271.75,
                        269.05,
                        266.38,
                        263.74,
                    ),
                    "volumes": (
                        0.36433854,
                        0.36798528,
                        0.37167812,
                        0.37540355,
                        0.37916129,
                    ),
                    "sides": ("buy", "buy", "buy", "buy", "buy"),
                },
                "trigger_rapid_price_drop": {
                    "new_price": 260.0,
                    "prices": (277.21, 274.46, 271.74, 269.04, 266.37),
                    "volumes": (
                        0.3605931,
                        0.36420613,
                        0.36785168,
                        0.37154332,
                        0.37526754,
                    ),
                    "sides": ("sell", "sell", "sell", "sell", "sell"),
                },
                "trigger_all_sell_orders": {
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
                    "sell_volumes": (0.3605931,),
                },
                "check_not_enough_funds_for_sell": {
                    "sell_price": 272.0,
                    "n_orders": 5,
                    "n_sell_orders": 1,
                    "assume_base_available": 0.0,
                    "assume_quote_available": 1000.0,
                },
                "sell_after_not_enough_funds_for_sell": {
                    "price": 272.0,
                    "n_orders": 7,
                    "sell_prices": (277.21, 274.99),
                    "sell_volumes": (0.3605931, 0.36350418),
                },
                "check_max_investment_reached": {
                    "current_price": 270.0,
                    "n_open_sell_orders": 2,
                    "max_investment": 202.0,
                },
            },
        ),
    ],
    ids=("BTCUSD", "AAPLxUSD"),
)
async def test_kraken_grid_hodl(  # noqa: PLR0913,PLR0917
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    mock_sleep3: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    notification_config: NotificationConfigDTO,
    db_config: DBConfigDTO,
    bot_config: BotConfigDTO,
    kraken_config: KrakenExchangeAPIConfig,
    expectations: dict,
) -> None:
    """
    Test the GridHODL strategy using pre-generated websocket messages.

    This one is very similar to GridSell, the main difference is the volume of
    sell orders.
    """
    LOG.info("******* Starting GridHODL integration test *******")
    caplog.set_level(logging.INFO)

    tm = KrakenTestManager(
        bot_config=bot_config,
        notification_config=notification_config,
        db_config=db_config,
        kraken_config=kraken_config,
    )
    await tm.initialize_engine()
    await tm.trigger_prepare_for_trading(initial_ticker=expectations["initial_ticker"])

    # ==========================================================================
    # 1. PLACEMENT OF INITIAL N BUY ORDERS
    await tm.check_initial_n_buy_orders(
        prices=expectations["check_initial_n_buy_orders"]["prices"],
        volumes=expectations["check_initial_n_buy_orders"]["volumes"],
        sides=expectations["check_initial_n_buy_orders"]["sides"],
    )

    # ==========================================================================
    # 2. SHIFTING UP BUY ORDERS
    await tm.trigger_shift_up_buy_orders(
        new_price=expectations["trigger_shift_up_buy_orders"]["new_price"],
        prices=expectations["trigger_shift_up_buy_orders"]["prices"],
        volumes=expectations["trigger_shift_up_buy_orders"]["volumes"],
        sides=expectations["trigger_shift_up_buy_orders"]["sides"],
    )

    # ==========================================================================
    # 3. FILLING A BUY ORDER
    await tm.trigger_fill_buy_order(
        no_trigger_price=expectations["trigger_fill_buy_order"]["no_trigger_price"],
        new_price=expectations["trigger_fill_buy_order"]["new_price"],
        old_prices=expectations["trigger_fill_buy_order"]["old_prices"],
        old_volumes=expectations["trigger_fill_buy_order"]["old_volumes"],
        old_sides=expectations["trigger_fill_buy_order"]["old_sides"],
        new_prices=expectations["trigger_fill_buy_order"]["new_prices"],
        new_volumes=expectations["trigger_fill_buy_order"]["new_volumes"],
        new_sides=expectations["trigger_fill_buy_order"]["new_sides"],
    )

    # ==========================================================================
    # 4. ENSURING N OPEN BUY ORDERS
    await tm.trigger_ensure_n_open_buy_orders(
        new_price=expectations["trigger_ensure_n_open_buy_orders"]["new_price"],
        prices=expectations["trigger_ensure_n_open_buy_orders"]["prices"],
        volumes=expectations["trigger_ensure_n_open_buy_orders"]["volumes"],
        sides=expectations["trigger_ensure_n_open_buy_orders"]["sides"],
    )

    # ==========================================================================
    # 5. FILLING A SELL ORDER
    # Now let's see if the sell order gets triggered.
    await tm.trigger_fill_sell_order(
        new_price=expectations["trigger_fill_sell_order"]["new_price"],
        prices=expectations["trigger_fill_sell_order"]["prices"],
        volumes=expectations["trigger_fill_sell_order"]["volumes"],
        sides=expectations["trigger_fill_sell_order"]["sides"],
    )
    # ... as we can see, the sell order got removed from the orderbook.
    # ... there is no new corresponding buy order placed - this would only be
    # the case for the case, if there would be more sell orders.
    # As usual, if the price would rise higher, the buy orders would shift up.

    # ==========================================================================
    # 6. RAPID PRICE DROP - FILLING ALL BUY ORDERS
    await tm.trigger_rapid_price_drop(
        new_price=expectations["trigger_rapid_price_drop"]["new_price"],
        prices=expectations["trigger_rapid_price_drop"]["prices"],
        volumes=expectations["trigger_rapid_price_drop"]["volumes"],
        sides=expectations["trigger_rapid_price_drop"]["sides"],
    )

    # ==========================================================================
    # 7. SELL ALL AND ENSURE N OPEN BUY ORDERS
    await tm.trigger_all_sell_orders(
        new_price=expectations["trigger_all_sell_orders"]["new_price"],
        buy_prices=expectations["trigger_all_sell_orders"]["buy_prices"],
        sell_prices=expectations["trigger_all_sell_orders"]["sell_prices"],
        buy_volumes=expectations["trigger_all_sell_orders"]["buy_volumes"],
        sell_volumes=expectations["trigger_all_sell_orders"]["sell_volumes"],
    )

    # ==========================================================================
    # 8. Test what happens if there are not enough funds to place a sell order
    #    for some reason.
    await tm.check_not_enough_funds_for_sell(
        sell_price=expectations["check_not_enough_funds_for_sell"]["sell_price"],
        n_orders=expectations["check_not_enough_funds_for_sell"]["n_orders"],
        n_sell_orders=expectations["check_not_enough_funds_for_sell"]["n_sell_orders"],
        assume_base_available=expectations["check_not_enough_funds_for_sell"][
            "assume_base_available"
        ],
        assume_quote_available=expectations["check_not_enough_funds_for_sell"][
            "assume_quote_available"
        ],
        fail=False,
    )

    # ==========================================================================
    # 9. Check sell of surplus
    LOG.info("******* Check filling surplus *******")
    api = tm.ws_client.__websocket_service

    # The following ticker update will place a new buy order as well as placing
    # the missed sell order since the balance is now sufficient due to reset of
    # the earlier mock.
    await api.on_ticker_update(
        callback=tm.ws_client.on_message,
        last=expectations["sell_after_not_enough_funds_for_sell"]["price"],
    )
    assert (
        tm.strategy._orderbook_table.count()
        == expectations["sell_after_not_enough_funds_for_sell"]["n_orders"]
    )
    for order, price, volume in zip(
        (tm.strategy._orderbook_table.get_orders(filters={"side": "sell"}).all()),
        expectations["sell_after_not_enough_funds_for_sell"]["sell_prices"],
        expectations["sell_after_not_enough_funds_for_sell"]["sell_volumes"],
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume

    # ==========================================================================
    # 9. MAX INVESTMENT REACHED
    await tm.check_max_investment_reached(
        current_price=expectations["check_max_investment_reached"]["current_price"],
        n_open_sell_orders=expectations["check_max_investment_reached"][
            "n_open_sell_orders"
        ],
        max_investment=expectations["check_max_investment_reached"]["max_investment"],
    )


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_hodl.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
async def test_kraken_grid_hodl_unfilled_surplus(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.Mock,  # noqa: ARG001
    mock_sleep3: mock.Mock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    kraken_gridhodl_bot_config: BotConfigDTO,
    notification_config: NotificationConfigDTO,
    db_config: DBConfigDTO,
    kraken_config_xbtusd: KrakenExchangeAPIConfig,
) -> None:
    """
    Integration test for the GridHODL strategy using pre-generated websocket
    messages.

    This test checks if the unfilled surplus is handled correctly.

    unfilled surplus: The base currency volume that was partly filled by an buy
    order, before the order was cancelled.
    """
    LOG.info("******* Starting GridHODL unfilled surplus integration test *******")
    caplog.set_level(logging.INFO)

    tm = KrakenTestManager(
        bot_config=kraken_gridhodl_bot_config,
        notification_config=notification_config,
        db_config=db_config,
        kraken_config=kraken_config_xbtusd,
    )
    await tm.initialize_engine()
    await tm.trigger_prepare_for_trading(initial_ticker=50_000.0)

    # ==========================================================================
    # 1. PLACEMENT OF INITIAL N BUY ORDERS
    await tm.check_initial_n_buy_orders(
        prices=(49_504.9, 49_014.7, 48_529.4, 48_048.9, 47_573.1),
        volumes=(0.00202, 0.0020402, 0.0020606, 0.00208121, 0.00210202),
        sides=("buy", "buy", "buy", "buy", "buy"),
    )

    # ==========================================================================
    # 2. BUYING PARTLY FILLED and ensure that the unfilled surplus is handled
    LOG.info("******* Check partially filled orders *******")
    api = tm.ws_client.__websocket_service

    api.fill_order(tm.strategy._orderbook_table.get_orders().first().txid, 0.002)
    assert tm.strategy._orderbook_table.count() == 5

    balances = api.get_balances()
    assert Decimal(balances[kraken_config_xbtusd.base_currency]["balance"]) == Decimal(
        "100.002",
    )
    assert float(
        balances[kraken_config_xbtusd.quote_currency]["balance"],
    ) == pytest.approx(999_400.99)

    tm.strategy._handle_cancel_order(
        tm.strategy._orderbook_table.get_orders().first().txid,
    )

    assert tm.strategy._configuration_table.get()["vol_of_unfilled_remaining"] == 0.002
    assert (
        tm.strategy._configuration_table.get()["vol_of_unfilled_remaining_max_price"]
        == 49_504.9
    )

    # ==========================================================================
    # 3. SELLING THE UNFILLED SURPLUS
    #    The sell-check is done only during cancelling orders, as this is the
    #    only time where this amount is touched. So we need to create another
    #    partly filled order.
    LOG.info("******* Check selling the unfilled surplus *******")

    tm.strategy.new_buy_order(order_price=49_504.9)
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
        == 5
    )

    order = tm.strategy._orderbook_table.get_orders(filters={"price": 49_504.9}).all()[
        0
    ]
    api.fill_order(order["txid"], 0.002)
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
        == 5
    )
    assert (
        tm.strategy._configuration_table.get()["vol_of_unfilled_remaining_max_price"]
        == 0.0
    )

    sell_orders = tm.strategy._orderbook_table.get_orders(
        filters={"side": "sell"},
    ).all()
    assert sell_orders[0].price == 50_500.0
    assert sell_orders[0].volume == pytest.approx(0.00199014)
