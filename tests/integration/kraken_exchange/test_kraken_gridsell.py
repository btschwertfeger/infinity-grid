# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Integration tests for the GridSell strategy on Kraken exchange."""

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
def kraken_gridsell_bot_config() -> BotConfigDTO:
    return BotConfigDTO(
        strategy="GridSell",
        exchange="Kraken",
        api_public_key="",
        api_secret_key="",
        name="Local Tests Bot GridSell",
        userref=0,
        base_currency="BTC",
        quote_currency="USD",
        max_investment=10000.0,
        amount_per_grid=100.0,
        interval=0.01,
        n_open_buy_orders=5,
    )


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_sell.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
async def test_kraken_grid_sell(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    mock_sleep3: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    kraken_gridsell_bot_config: BotConfigDTO,
    notification_config: NotificationConfigDTO,
    db_config: DBConfigDTO,
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

    # Create engine using mocked Kraken API
    engine = await get_kraken_instance(
        bot_config=kraken_gridsell_bot_config,
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
    LOG.info("******* Check placement of initial buy orders *******")

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
    LOG.info("******* Check shifting up buy orders works *******")
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
    LOG.info("******* Check filling a buy order works *******")
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
    assert strategy._orderbook_table.count() == 5

    # Ensure that we have 4 buy orders and 1 sell order
    for order, price, volume, side in zip(
        strategy._orderbook_table.get_orders().all(),
        (58817.7, 58235.3, 57658.7, 57087.8, 59999.9),
        (0.00170016, 0.00171717, 0.00173434, 0.00175168, 0.00168333),
        ["buy"] * 4 + ["sell"],
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == side
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    # ==========================================================================
    # 4. ENSURING N OPEN BUY ORDERS
    LOG.info("******* Check ensuring N open buy orders works *******")
    # If there is a new price event, the algorithm will place the 5th buy order.
    await api.on_ticker_update(callback=ws_client.on_message, last=59100.0)
    assert state_machine.state == States.RUNNING
    assert strategy._orderbook_table.count() == 6

    for order, price, volume, side in zip(
        strategy._orderbook_table.get_orders().all(),
        (58817.7, 58235.3, 57658.7, 57087.8, 59999.9, 56522.5),
        (0.00170016, 0.00171717, 0.00173434, 0.00175168, 0.00168333, 0.0017692),
        ["buy"] * 4 + ["sell"] + ["buy"],
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == side
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    # ==========================================================================
    # 5. FILLING A SELL ORDER
    LOG.info("******* Check filling a sell order works *******")
    # Now let's see if the sell order gets triggered.
    await api.on_ticker_update(callback=ws_client.on_message, last=60000.0)
    assert state_machine.state == States.RUNNING
    assert strategy._orderbook_table.count() == 5

    for order, price, volume, side in zip(
        strategy._orderbook_table.get_orders().all(),
        (58817.7, 58235.3, 57658.7, 57087.8, 56522.5),
        (0.00170016, 0.00171717, 0.00173434, 0.00175168, 0.0017692),
        ["buy"] * 5,
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == side
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    # ... as we can see, the sell order got removed from the orderbook.
    # ... there is no new corresponding buy order placed - this would only be
    # the case for the case, if there would be more sell orders.
    # As usual, if the price would rise higher, the buy orders would shift up.

    # ==========================================================================
    # 6. RAPID PRICE DROP - FILLING ALL BUY ORDERS
    LOG.info("******* Check filling all buy due to rapid price drop *******")
    # Now check the behavior for a rapid price drop.
    await api.on_ticker_update(callback=ws_client.on_message, last=50000.0)
    assert state_machine.state == States.RUNNING
    assert strategy._orderbook_table.count() == 5

    for order, price, volume in zip(
        strategy._orderbook_table.get_orders().all(),
        (59405.8, 58817.6, 58235.2, 57658.6, 57087.7),
        (0.00170016, 0.00171717, 0.00173434, 0.00175168, 0.0017692),
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == "sell"
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    # ==========================================================================
    # 7. SELL ALL AND ENSURE N OPEN BUY ORDERS
    #    Here we temporarily have more than 5 buy orders, since every sell order
    #    triggers a new buy order, causing us to have 9 buy orders and a single
    #    sell order. Which is not a problem, since the buy orders that are too
    #    much will get canceled after the next price update.
    LOG.info(
        "******* Check filling all sell orders and ensuring N open buy orders *******",
    )
    await api.on_ticker_update(callback=ws_client.on_message, last=59100.0)
    assert state_machine.state == States.RUNNING
    assert strategy._orderbook_table.count() == 6
    current_orders = strategy._orderbook_table.get_orders().all()
    assert len(current_orders) == 6

    for order, price, volume in zip(
        strategy._orderbook_table.get_orders(filters={"side": "sell"}).all(),
        (59405.8,),
        (0.00170016,),
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == "sell"
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    for order, price, volume in zip(
        (o for o in current_orders if o.side == "buy"),
        (58514.8, 57935.4, 57361.7, 56793.7, 56231.3),
        (0.00170896, 0.00172606, 0.00174332, 0.00176075, 0.00177836),
        strict=True,
    ):
        assert order.price == price
        assert order.volume == volume
        assert order.side == "buy"
        assert order.symbol == "XBTUSD"
        assert order.userref == strategy._config.userref

    # ==========================================================================
    # 8. MAX INVESTMENT REACHED
    LOG.info("******* Check max investment reached behavior *******")

    # First ensure that new buy orders can be placed...
    assert not strategy._max_investment_reached
    strategy._GridStrategyBase__cancel_all_open_buy_orders()
    assert strategy._orderbook_table.count() == 1
    await api.on_ticker_update(callback=ws_client.on_message, last=50000.0)
    assert strategy._orderbook_table.count() == 6

    # Now with a different max investment, the max investment should be reached
    # and no further orders be placed.
    assert not strategy._max_investment_reached
    old_max_investment = strategy._config.max_investment
    strategy._config.max_investment = 202.0  # 200 USD + fee
    strategy._GridStrategyBase__cancel_all_open_buy_orders()
    assert strategy._orderbook_table.count() == 1
    await api.on_ticker_update(callback=ws_client.on_message, last=50000.0)
    assert strategy._orderbook_table.count() == 2
    assert strategy._max_investment_reached
    assert state_machine.state == States.RUNNING
    strategy._config.max_investment = old_max_investment

    # ==========================================================================
    # 9. Test what happens if there are not enough funds to place a sell order
    #    for some reason. The GridSell strategy will fail in this case to trigger
    #    a restart (handled by external process manager)
    LOG.info("******* Check not enough funds for sell order *******")
    # Ensure buy orders exist
    await api.on_ticker_update(callback=ws_client.on_message, last=58500.0)
    assert strategy._orderbook_table.count() == 6  # 5 buy and one sell order
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
        await api.on_ticker_update(callback=ws_client.on_message, last=57900.0)
        assert state_machine.state == States.ERROR
        assert strategy._orderbook_table.count() != 5
        assert (
            len(strategy._orderbook_table.get_orders(filters={"side": "sell"}).all())
            == 1
        )
        assert "Not enough" in caplog.text
    finally:
        # Restore the original method
        strategy._rest_api.get_pair_balance = original_get_pair_balance


@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_sell.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
async def test_kraken_grid_sell_unfilled_surplus(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.Mock,  # noqa: ARG001
    mock_sleep3: mock.Mock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    kraken_gridsell_bot_config: BotConfigDTO,
    notification_config: NotificationConfigDTO,
    db_config: DBConfigDTO,
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

    # Create engine using mocked Kraken API
    engine = await get_kraken_instance(
        bot_config=kraken_gridsell_bot_config,
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
    # 2. BUYING PARTLY FILLED and ensure that the unfilled surplus is handled
    LOG.info("******* Check partially filled orders *******")

    api.fill_order(strategy._orderbook_table.get_orders().first().txid, 0.002)
    assert strategy._orderbook_table.count() == 5

    balances = api.get_balances()
    assert balances["XXBT"]["balance"] == "100.002"
    assert float(balances["ZUSD"]["balance"]) == pytest.approx(999400.99)

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
    assert strategy._orderbook_table.count() == 5
    assert (
        len(
            [
                o
                for o in rest_api.get_open_orders(userref=strategy._config.userref)
                if o.status == "open"
            ],
        )
        == 5
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
        == 5
    )
    assert (
        strategy._configuration_table.get()["vol_of_unfilled_remaining_max_price"]
        == 0.0
    )

    sell_orders = strategy._orderbook_table.get_orders(filters={"side": "sell"}).all()
    assert sell_orders[0].price == 50500.0
    assert sell_orders[0].volume == pytest.approx(0.00199014)
