# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

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


@pytest.fixture
def kraken_cdca_bot_config() -> BotConfigDTO:
    return BotConfigDTO(
        strategy="cDCA",
        exchange="Kraken",
        api_public_key="",
        api_secret_key="",
        name="Local Tests Bot cDCA",
        userref=0,
        base_currency="BTC",  # AAPLx
        quote_currency="USD",
        max_investment=10000.0,
        amount_per_grid=100.0,
        interval=0.01,
        n_open_buy_orders=5,
        verbosity=0,
    )


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
async def test_kraken_cdca(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    kraken_cdca_bot_config: BotConfigDTO,
    notification_config: NotificationConfigDTO,
    db_config: DBConfigDTO,
) -> None:
    """
    Integration test for cDCA strategy using pre-generated websocket messages.
    """
    caplog.set_level(logging.INFO)

    # Create engine using mocked Kraken API
    engine = await get_kraken_instance(
        bot_config=kraken_cdca_bot_config,
        notification_config=notification_config,
        db_config=db_config,
        base_currency="XBT",
        quote_currency="ZUSD",
        pair="XBTUSD",
        ws_symbol="BTC/USD",
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

    # Check if the five initial buy orders are placed with the expected price
    # and volume. Note that the interval is not exactly 0.01 due to the fee
    # which is taken into account.
    for order, price, volume in zip(
        strategy._orderbook_table.get_orders().all(),
        (49504.9, 49014.7, 48529.4, 48048.9, 47573.1),
        (0.00202, 0.0020402, 0.0020606, 0.00208121, 0.00210202),
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == "buy"
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    # ==========================================================================
    # 2. SHIFTING UP BUY ORDERS
    # Check if shifting up the buy orders works
    await api.on_ticker_update(callback=ws_client.on_message, last=60000.0)
    assert strategy._ticker == 60000.0
    assert state_machine.state == States.RUNNING

    # We should now still have 5 buy orders, but at a higher price. The other
    # orders should be canceled.
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

    # ==========================================================================
    # 3. FILLING A BUY ORDER
    # Now lets let the price drop a bit so that a buy order gets triggered.
    await api.on_ticker_update(callback=ws_client.on_message, last=59990.0)
    assert strategy._ticker == 59990.0
    assert state_machine.state == States.RUNNING

    # Quick re-check ... the price update should not affect any orderbook
    # changes when dropping.
    for order, price, volume in zip(
        strategy._orderbook_table.get_orders().all(),
        (59405.9, 58817.7, 58235.3, 57658.7, 57087.8),
        (0.00168333, 0.00170016, 0.00171717, 0.00173434, 0.00175168),
        strict=False,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == "buy"
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    assert strategy._orderbook_table.count() == 5

    # Now trigger the execution of the first buy order
    await api.on_ticker_update(callback=ws_client.on_message, last=59000.0)
    assert state_machine.state == States.RUNNING
    assert strategy._orderbook_table.count() == 4

    # Ensure that we have 4 buy orders and no sell order
    for order, price, volume in zip(
        strategy._orderbook_table.get_orders().all(),
        (58817.7, 58235.3, 57658.7, 57087.8),
        (0.00170016, 0.00171717, 0.00173434, 0.00175168),
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == "buy"
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    # ==========================================================================
    # 4. ENSURING N OPEN BUY ORDERS
    # If there is a new price event, the algorithm will place the 5th buy order.
    await api.on_ticker_update(callback=ws_client.on_message, last=59100.0)
    assert state_machine.state == States.RUNNING
    assert strategy._orderbook_table.count() == 5

    for order, price, volume in zip(
        strategy._orderbook_table.get_orders().all(),
        (58817.7, 58235.3, 57658.7, 57087.8, 56522.5),
        (0.00170016, 0.00171717, 0.00173434, 0.00175168, 0.0017692),
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == "buy"
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    # ==========================================================================
    # 5. RAPID PRICE DROP - FILLING ALL BUY ORDERS
    # Now check the behavior for a rapid price drop.
    await api.on_ticker_update(callback=ws_client.on_message, last=50000.0)
    assert state_machine.state == States.RUNNING
    assert strategy._orderbook_table.count() == 0
    assert rest_api.get_open_orders(userref=strategy._config.userref) == []

    # ==========================================================================
    # 6. ENSURE N OPEN BUY ORDERS
    await api.on_ticker_update(callback=ws_client.on_message, last=50100.0)
    assert state_machine.state == States.RUNNING
    assert strategy._orderbook_table.count() == 5

    for order, price, volume in zip(
        strategy._orderbook_table.get_orders().all(),
        (49603.9, 49112.7, 48626.4, 48144.9, 47668.2),
        (0.00201597, 0.00203613, 0.00205649, 0.00207706, 0.00209783),
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == "buy"
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    # ==========================================================================
    # 7. MAX INVESTMENT REACHED

    # First ensure that new buy orders can be placed...
    assert not strategy._max_investment_reached
    strategy._GridStrategyBase__cancel_all_open_buy_orders()
    assert strategy._orderbook_table.count() == 0
    await api.on_ticker_update(callback=ws_client.on_message, last=50000.0)
    assert strategy._orderbook_table.count() == 5

    # Now with a different max investment, the max investment should be reached
    # and no further orders be placed.
    assert not strategy._max_investment_reached
    strategy._config.max_investment = 202.0  # 200 USD + fee
    strategy._GridStrategyBase__cancel_all_open_buy_orders()
    assert strategy._orderbook_table.count() == 0
    await api.on_ticker_update(callback=ws_client.on_message, last=50000.0)
    assert strategy._orderbook_table.count() == 2
    assert strategy._max_investment_reached

    assert state_machine.state == States.RUNNING
