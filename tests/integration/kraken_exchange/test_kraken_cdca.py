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

from .helper import KrakenTestManager
from .kraken_exchange_api import KrakenExchangeAPIConfig


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
    kraken_config_xbtusd: KrakenExchangeAPIConfig,
) -> None:
    """
    Integration test for cDCA strategy using pre-generated websocket messages.
    """
    caplog.set_level(logging.INFO)

    tm = KrakenTestManager(
        bot_config=kraken_cdca_bot_config,
        notification_config=notification_config,
        db_config=db_config,
        kraken_config=kraken_config_xbtusd,
    )
    await tm.initialize_engine()

    state_machine = tm.state_machine
    strategy = tm.strategy
    ws_client = tm.ws_client
    rest_api = tm.rest_api
    api = tm.api

    # ==========================================================================
    # During the following processing, the following steps are done:
    # 1. The algorithm prepares for trading (see setup)
    # 2. The order manager checks the price range
    # 3. The order manager checks for n open buy orders
    # 4. The order manager places new orders
    await tm.trigger_prepare_for_trading(initial_ticker=50_000.0)

    # ==========================================================================
    # 1. PLACEMENT OF INITIAL N BUY ORDERS
    await tm.check_initial_n_buy_orders(
        prices=(49504.9, 49014.7, 48529.4, 48048.9, 47573.1),
        volumes=(0.00202, 0.0020402, 0.0020606, 0.00208121, 0.00210202),
    )

    # ==========================================================================
    # 2. SHIFTING UP BUY ORDERS
    # Check if shifting up the buy orders works
    await tm.trigger_shift_up_buy_orders(
        new_price=60_000.0,
        prices=(59405.9, 58817.7, 58235.3, 57658.7, 57087.8),
        volumes=(0.00168333, 0.00170016, 0.00171717, 0.00173434, 0.00175168),
    )
    # ==========================================================================
    # 3. FILLING A BUY ORDER
    # Now lets let the price drop a bit so that a buy order gets triggered.
    await tm.trigger_fill_buy_order(
        no_trigger_price=59_990.0,
        new_price=59_000.0,
        old_prices=(59405.9, 58817.7, 58235.3, 57658.7, 57087.8),
        old_volumes=(0.00168333, 0.00170016, 0.00171717, 0.00173434, 0.00175168),
        old_sides=("buy", "buy", "buy", "buy", "buy"),
        new_prices=(58817.7, 58235.3, 57658.7, 57087.8),
        new_volumes=(0.00170016, 0.00171717, 0.00173434, 0.00175168),
        new_sides=("buy", "buy", "buy", "buy"),
    )

    # ==========================================================================
    # 4. ENSURING N OPEN BUY ORDERS
    await tm.trigger_ensure_n_open_buy_orders(
        new_price=59_100.0,
        prices=(58817.7, 58235.3, 57658.7, 57087.8, 56522.5),
        volumes=(0.00170016, 0.00171717, 0.00173434, 0.00175168, 0.0017692),
        sides=("buy", "buy", "buy", "buy", "buy"),
    )

    # ==========================================================================
    # 5. RAPID PRICE DROP - FILLING ALL BUY ORDERS
    # Now check the behavior for a rapid price drop.
    await tm.trigger_rapid_price_drop(
        new_price=50_000.0,
        prices=(),
        volumes=(),
        sides=(),
    )

    # ==========================================================================
    # 6. ENSURE N OPEN BUY ORDERS ... after rapid price drop has filled all buy
    #    orders
    await tm.trigger_ensure_n_open_buy_orders(
        new_price=50_100.0,
        prices=(49603.9, 49112.7, 48626.4, 48144.9, 47668.2),
        volumes=(0.00201597, 0.00203613, 0.00205649, 0.00207706, 0.00209783),
        sides=("buy", "buy", "buy", "buy", "buy"),
    )

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
