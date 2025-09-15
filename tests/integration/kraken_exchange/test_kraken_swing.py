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

from infinity_grid.core.state_machine import States
from infinity_grid.models.configuration import (
    BotConfigDTO,
    DBConfigDTO,
    NotificationConfigDTO,
)

from .helper import get_kraken_instance

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
        max_investment=10000.0,
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
) -> None:
    """
    Integration test for the SWING strategy using pre-generated websocket
    messages.
    """
    LOG.info("******* Starting SWING integration test *******")
    caplog.set_level(logging.DEBUG)

    # Create engine using mocked Kraken API
    engine = await get_kraken_instance(
        bot_config=kraken_swing_bot_config,
        notification_config=notification_config,
        db_config=db_config,
    )
    state_machine = engine._BotEngine__state_machine
    strategy = engine._BotEngine__strategy
    ws_client = strategy._GridHODLStrategy__ws_client
    api = engine._BotEngine__strategy._GridHODLStrategy__ws_client.__websocket_service

    # ==========================================================================
    # During the following processing, the following steps are done:
    # 1. The algorithm prepares for trading (see setup)
    # 2. The order manager checks the price range
    # 3. The order manager checks for n open buy orders
    # 4. The order manager places new orders
    await ws_client.on_message(
        {
            "channel": "executions",
            "type": "snapshot",
            "data": [{"exec_type": "canceled", "order_id": "txid0"}],
        },
    )
    assert state_machine.state == States.INITIALIZING
    assert strategy._ready_to_trade is False

    await api.on_ticker_update(callback=ws_client.on_message, last=50000.0)
    assert strategy._ticker == 50000.0
    assert state_machine.state == States.RUNNING
    assert strategy._ready_to_trade is True

    # ==========================================================================
    # 1. PLACEMENT OF INITIAL N BUY ORDERS
    # After both fake-websocket channels are connected, the algorithm went
    # through its full setup and placed orders against the fake Kraken API and
    # finally saved those results into the local orderbook table.
    # The SWING strategy additionally starts selling the existing base currency
    # at defined intervals.
    LOG.info("******* Check placement of initial buy orders *******")

    for order, price, volume, side in zip(
        strategy._orderbook_table.get_orders().all(),
        (49504.9, 49014.7, 48529.4, 48048.9, 47573.1, 51005.0),
        (0.00202, 0.0020402, 0.0020606, 0.00208121, 0.00210202, 0.00197044),
        ["buy"] * 5 + ["sell"],
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == side
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    # ==========================================================================
    # 2. RAPID PRICE DROP - FILLING ALL BUY ORDERS + CREATING SELL ORDERS
    # Now check the behavior for a rapid price drop.
    # It should fill the buy orders and place 6 new sell orders.

    await api.on_ticker_update(callback=ws_client.on_message, last=40000.0)
    assert strategy._ticker == 40000.0
    assert state_machine.state == States.RUNNING

    for order, price, volume in zip(
        strategy._orderbook_table.get_orders().all(),
        (51005.0, 49999.9, 49504.8, 49014.6, 48529.3, 48048.8),
        (0.00197044, 0.00201005, 0.00203015, 0.00205046, 0.00207096, 0.00209167),
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == "sell"
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    # ==========================================================================
    # 3. NEW TICKER TO ENSURE N OPEN BUY ORDERS
    LOG.info("******* Check ensuring N open buy orders *******")
    await api.on_ticker_update(callback=ws_client.on_message, last=40000.1)
    assert state_machine.state == States.RUNNING

    for order, price, volume in zip(
        strategy._orderbook_table.get_orders(filters={"side": "sell"}).all(),
        (51005.0, 49999.9, 49504.8, 49014.6, 48529.3, 48048.8),
        (0.00197044, 0.00201005, 0.00203015, 0.00205046, 0.00207096, 0.00209167),
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == "sell"
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    for order, price, volume in zip(
        strategy._orderbook_table.get_orders(filters={"side": "buy"}).all(),
        (39604.0, 39211.8, 38823.5, 38439.1, 38058.5),
        (0.00252499, 0.00255025, 0.00257575, 0.00260151, 0.00262753),
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == "buy"
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    # ==========================================================================
    # 4. FILLING SELL ORDERS WHILE SHIFTING UP BUY ORDERS
    LOG.info("******* Check filling sell orders while shifting up buy orders *******")
    # Check if shifting up the buy orders works
    quote_balance_before = float(api.get_balances()["ZUSD"]["balance"])
    base_balance_before = float(api.get_balances()["XXBT"]["balance"])

    await api.on_ticker_update(callback=ws_client.on_message, last=60000.0)
    assert state_machine.state == States.RUNNING

    for order, price, volume in zip(
        strategy._orderbook_table.get_orders().all(),
        (59405.9, 58817.7, 58235.3, 57658.7, 57087.8),
        (0.00168333, 0.00170016, 0.00171717, 0.00173434, 0.00175168),
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == "buy"
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    # Ensure that profit has been made
    assert float(api.get_balances()["ZUSD"]["balance"]) > quote_balance_before
    assert float(api.get_balances()["XXBT"]["balance"]) < base_balance_before

    # ==========================================================================
    # 5. Test what happens if there are not enough funds to place a sell order
    #    for some reason.
    LOG.info("******* Check not enough funds for sell order *******")

    # Save the original method to restore it later
    original_get_pair_balance = strategy._rest_api.get_pair_balance

    # Mock the instance method directly
    strategy._rest_api.get_pair_balance = mock.Mock(
        return_value=mock.Mock(
            base_available=0.000,
            quote_available=1000.0,
        ),
    )

    try:
        # Now trigger the sell order
        await api.on_ticker_update(callback=ws_client.on_message, last=59000.0)
        assert state_machine.state == States.RUNNING
        assert strategy._orderbook_table.count() == 4
        assert (
            len(strategy._orderbook_table.get_orders(filters={"side": "sell"}).all())
            == 0
        )
        assert "Not enough funds" in caplog.text
    finally:
        # Restore the original method
        strategy._rest_api.get_pair_balance = original_get_pair_balance


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

    # Create engine using mocked Kraken API
    engine = await get_kraken_instance(
        bot_config=kraken_swing_bot_config,
        notification_config=notification_config,
        db_config=db_config,
    )
    state_machine = engine._BotEngine__state_machine
    strategy = engine._BotEngine__strategy
    ws_client = strategy._GridHODLStrategy__ws_client
    rest_api = strategy._rest_api
    api = engine._BotEngine__strategy._GridHODLStrategy__ws_client.__websocket_service

    # ==========================================================================
    # During the following processing, the following steps are done:
    # 1. The algorithm prepares for trading (see setup)
    # 2. The order manager checks the price range
    # 3. The order manager checks for n open buy orders
    # 4. The order manager places new orders
    await ws_client.on_message(
        {
            "channel": "executions",
            "type": "snapshot",
            "data": [{"exec_type": "canceled", "order_id": "txid0"}],
        },
    )
    assert state_machine.state == States.INITIALIZING
    assert strategy._ready_to_trade is False

    await api.on_ticker_update(callback=ws_client.on_message, last=50000.0)
    assert strategy._ticker == 50000.0
    assert state_machine.state == States.RUNNING
    assert strategy._ready_to_trade is True

    # ==========================================================================
    # 1. PLACEMENT OF INITIAL N BUY ORDERS
    # After both fake-websocket channels are connected, the algorithm went
    # through its full setup and placed orders against the fake Kraken API and
    # finally saved those results into the local orderbook table.
    LOG.info("******* Check placement of initial buy orders *******")

    # Check if the five initial buy orders are placed with the expected price
    # and volume. Note that the interval is not exactly 0.01 due to the fee
    # which is taken into account.
    for order, price, volume, side in zip(
        strategy._orderbook_table.get_orders().all(),
        (49504.9, 49014.7, 48529.4, 48048.9, 47573.1, 51005.0),
        (0.00202, 0.0020402, 0.0020606, 0.00208121, 0.00210202, 0.00197044),
        ["buy"] * 5 + ["sell"],
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == side
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    balances = api.get_balances()
    assert float(balances["XXBT"]["balance"]) == pytest.approx(99.99802956)
    assert float(balances["XXBT"]["hold_trade"]) == pytest.approx(0.00197044)
    assert float(balances["ZUSD"]["balance"]) == pytest.approx(999500.0011705891)
    assert float(balances["ZUSD"]["hold_trade"]) == pytest.approx(499.99882941100003)

    # ==========================================================================
    # 2. BUYING PARTLY FILLED and ensure that the unfilled surplus is handled
    # correctly.
    LOG.info("******* Check handling of unfilled surplus *******")
    api.fill_order(strategy._orderbook_table.get_orders().first().txid, 0.002)
    assert strategy._orderbook_table.count() == 6

    # We have not 100.002 here, since the GridSell is initially creating a sell
    # order which reduces the available base balance.
    balances = api.get_balances()
    assert float(balances["XXBT"]["balance"]) == pytest.approx(100.00002956)
    assert float(balances["XXBT"]["hold_trade"]) == pytest.approx(0.00197044)
    assert float(balances["ZUSD"]["balance"]) == pytest.approx(999400.9913705891)
    assert float(balances["ZUSD"]["hold_trade"]) == pytest.approx(400.98902941100005)

    strategy._handle_cancel_order(
        strategy._orderbook_table.get_orders().first().txid,
    )

    assert strategy._configuration_table.get()["vol_of_unfilled_remaining"] == 0.002
    assert (
        strategy._configuration_table.get()["vol_of_unfilled_remaining_max_price"]
        == 49504.9
    )

    # ==========================================================================
    # 3. SELLING THE UNFILLED SURPLUS
    #    The sell-check is done only during cancelling orders, as this is the
    #    only time where this amount is touched. So we need to create another
    #    partly filled order.
    LOG.info("******* Check selling the unfilled surplus *******")
    strategy.new_buy_order(order_price=49504.9)
    assert strategy._orderbook_table.count() == 6
    assert (
        len(
            [
                o
                for o in rest_api.get_open_orders(userref=strategy._config.userref)
                if o.status == "open"
            ],
        )
        == 6
    )

    order = strategy._orderbook_table.get_orders(filters={"price": 49504.9}).all()[0]
    api.fill_order(order["txid"], 0.002)
    strategy._handle_cancel_order(order["txid"])

    assert (
        len(
            [
                o
                for o in rest_api.get_open_orders(userref=strategy._config.userref)
                if o.status == "open"
            ],
        )
        == 6
    )
    assert (
        strategy._configuration_table.get()["vol_of_unfilled_remaining_max_price"]
        == 0.0
    )

    sell_orders = strategy._orderbook_table.get_orders(
        filters={"side": "sell", "id": 7},
    ).all()
    assert sell_orders[0].price == 50500.0
    assert sell_orders[0].volume == pytest.approx(0.00199014)

    # ==========================================================================
    # 4. MAX INVESTMENT REACHED
    LOG.info("******* Check max investment reached behavior *******")

    # First ensure that new buy orders can be placed...
    assert not strategy._max_investment_reached
    strategy._GridStrategyBase__cancel_all_open_buy_orders()
    assert strategy._orderbook_table.count() == 2  # two sell orders
    await api.on_ticker_update(callback=ws_client.on_message, last=50000.0)
    assert strategy._orderbook_table.count() == 7  # 5 buy orders + 2 sell orders

    # Now with a different max investment, the max investment should be reached
    # and no further orders be placed.
    assert not strategy._max_investment_reached
    strategy._config.max_investment = 202.0  # 200 USD + fee
    strategy._GridStrategyBase__cancel_all_open_buy_orders()
    assert strategy._orderbook_table.count() == 2
    await api.on_ticker_update(callback=ws_client.on_message, last=50000.0)
    assert strategy._orderbook_table.count() == 2
    assert strategy._max_investment_reached

    assert state_machine.state == States.RUNNING
