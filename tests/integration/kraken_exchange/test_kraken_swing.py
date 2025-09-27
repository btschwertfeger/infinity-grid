# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Integration tests for the SWING strategy on Kraken exchange."""

import logging
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
def kraken_swing_bot_config() -> BotConfigDTO:
    return BotConfigDTO(
        strategy="SWING",
        exchange="Kraken",
        api_public_key="",
        api_secret_key="",
        name="Local Tests Bot Swing",
        userref=0,
        base_currency="BTC",
        quote_currency="USD",
        max_investment=10_000.0,
        amount_per_grid=100.0,
        interval=0.01,
        n_open_buy_orders=5,
        verbosity=0,
    )


@pytest.mark.wip
@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.swing.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
async def test_kraken_swing(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    mock_sleep3: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    kraken_swing_bot_config: BotConfigDTO,
    notification_config: NotificationConfigDTO,
    db_config: DBConfigDTO,
    kraken_config_xbtusd: KrakenExchangeAPIConfig,
) -> None:
    """
    Integration test for the SWING strategy using pre-generated websocket
    messages.
    """
    LOG.info("******* Starting SWING integration test *******")
    caplog.set_level(logging.DEBUG)

    tm = KrakenTestManager(
        bot_config=kraken_swing_bot_config,
        notification_config=notification_config,
        db_config=db_config,
        kraken_config=kraken_config_xbtusd,
    )
    await tm.initialize_engine()
    await tm.trigger_prepare_for_trading(initial_ticker=50_000.0)

    # ==========================================================================
    # 1. PLACEMENT OF INITIAL N BUY ORDERS
    await tm.check_initial_n_buy_orders(
        prices=(49_504.9, 49_014.7, 48_529.4, 48_048.9, 47_573.1, 51_005.0),
        volumes=(0.00202, 0.0020402, 0.0020606, 0.00208121, 0.00210202, 0.00197044),
        sides=("buy", "buy", "buy", "buy", "buy", "sell"),
    )

    # ==========================================================================
    # 2. RAPID PRICE DROP - FILLING ALL BUY ORDERS + CREATING SELL ORDERS
    # Now check the behavior for a rapid price drop.
    # It should fill the buy orders and place 6 new sell orders.
    await tm.trigger_rapid_price_drop(
        new_price=40_000.0,
        prices=(51_005.0, 49_999.9, 49_504.8, 49_014.6, 48_529.3, 48_048.8),
        volumes=(
            0.00197044,
            0.00201005,
            0.00203015,
            0.00205046,
            0.00207096,
            0.00209167,
        ),
        sides=("sell", "sell", "sell", "sell", "sell", "sell"),
    )

    # ==========================================================================
    # 3. NEW TICKER TO ENSURE N OPEN BUY ORDERS
    LOG.info("******* Check ensuring N open buy orders *******")
    await tm.trigger_ensure_n_open_buy_orders(
        new_price=40_000.1,
        prices=(
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
        volumes=(
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
        sides=(
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
    )

    # ==========================================================================
    # 4. FILLING SELL ORDERS WHILE SHIFTING UP BUY ORDERS
    # Check if shifting up the buy orders works
    api = tm.ws_client.__websocket_service

    base_balance_before = float(
        api.get_balances()[kraken_config_xbtusd.base_currency]["balance"],
    )
    quote_balance_before = float(
        api.get_balances()[kraken_config_xbtusd.quote_currency]["balance"],
    )

    await tm.trigger_shift_up_buy_orders(
        new_price=60_000.0,
        prices=(59_405.9, 58_817.7, 58_235.3, 57_658.7, 57_087.8),
        volumes=(0.00168333, 0.00170016, 0.00171717, 0.00173434, 0.00175168),
        sides=("buy", "buy", "buy", "buy", "buy"),
    )

    # Ensure that profit has been made
    assert (
        float(api.get_balances()[kraken_config_xbtusd.base_currency]["balance"])
        < base_balance_before
    )
    assert (
        float(api.get_balances()[kraken_config_xbtusd.quote_currency]["balance"])
        > quote_balance_before
    )

    # ==========================================================================
    # 5. Test what happens if there are not enough funds to place a sell order
    #    for some reason.
    await tm.check_not_enough_funds_for_sell(
        sell_price=59_000.0,
        n_orders=4,
        n_sell_orders=0,
        assume_base_available=0.0,
        assume_quote_available=1_000.0,
        fail=False,
    )


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.swing.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
async def test_kraken_swing_unfilled_surplus(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.Mock,  # noqa: ARG001
    mock_sleep3: mock.Mock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    kraken_swing_bot_config: BotConfigDTO,
    notification_config: NotificationConfigDTO,
    db_config: DBConfigDTO,
    kraken_config_xbtusd: KrakenExchangeAPIConfig,
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

    tm = KrakenTestManager(
        bot_config=kraken_swing_bot_config,
        notification_config=notification_config,
        db_config=db_config,
        kraken_config=kraken_config_xbtusd,
    )
    await tm.initialize_engine()
    await tm.trigger_prepare_for_trading(initial_ticker=50_000.0)

    # ==========================================================================
    # 1. PLACEMENT OF INITIAL N BUY ORDERS
    await tm.check_initial_n_buy_orders(
        prices=(49_504.9, 49_014.7, 48_529.4, 48_048.9, 47_573.1, 51_005.0),
        volumes=(0.00202, 0.0020402, 0.0020606, 0.00208121, 0.00210202, 0.00197044),
        sides=("buy", "buy", "buy", "buy", "buy", "sell"),
    )
    api = tm.ws_client.__websocket_service

    balances = api.get_balances()
    assert float(
        balances[kraken_config_xbtusd.base_currency]["balance"],
    ) == pytest.approx(99.99802956)
    assert float(
        balances[kraken_config_xbtusd.base_currency]["hold_trade"],
    ) == pytest.approx(0.00197044)
    assert float(
        balances[kraken_config_xbtusd.quote_currency]["balance"],
    ) == pytest.approx(999_500.0011705891)
    assert float(
        balances[kraken_config_xbtusd.quote_currency]["hold_trade"],
    ) == pytest.approx(499.99882941100003)

    # ==========================================================================
    # 2. BUYING PARTLY FILLED and ensure that the unfilled surplus is handled
    # correctly.
    LOG.info("******* Check handling of unfilled surplus *******")
    api.fill_order(tm.strategy._orderbook_table.get_orders().first().txid, 0.002)
    assert tm.strategy._orderbook_table.count() == 6

    # We have not 100.002 here, since the GridSell is initially creating a sell
    # order which reduces the available base balance.
    balances = api.get_balances()
    assert float(
        balances[kraken_config_xbtusd.base_currency]["balance"],
    ) == pytest.approx(100.00002956)
    assert float(
        balances[kraken_config_xbtusd.base_currency]["hold_trade"],
    ) == pytest.approx(0.00197044)
    assert float(
        balances[kraken_config_xbtusd.quote_currency]["balance"],
    ) == pytest.approx(999_400.9913705891)
    assert float(
        balances[kraken_config_xbtusd.quote_currency]["hold_trade"],
    ) == pytest.approx(400.98902941100005)

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
    assert tm.strategy._orderbook_table.count() == 6
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
        == 6
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
        == 6
    )
    assert (
        tm.strategy._configuration_table.get()["vol_of_unfilled_remaining_max_price"]
        == 0.0
    )

    sell_orders = tm.strategy._orderbook_table.get_orders(
        filters={"side": "sell", "id": 7},
    ).all()
    assert sell_orders[0].price == 50_500.0
    assert sell_orders[0].volume == pytest.approx(0.00199014)

    # ==========================================================================
    # 4. MAX INVESTMENT REACHED
    await tm.check_max_investment_reached(current_price=50_000.0, n_open_sell_orders=2)
