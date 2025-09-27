# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

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


@pytest.fixture
def kraken_cdca_bot_config() -> BotConfigDTO:
    return BotConfigDTO(
        strategy="cDCA",
        exchange="Kraken",
        api_public_key="",
        api_secret_key="",
        name="Local Tests Bot cDCA",
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
    await tm.trigger_prepare_for_trading(initial_ticker=50_000.0)

    # ==========================================================================
    # 1. PLACEMENT OF INITIAL N BUY ORDERS
    await tm.check_initial_n_buy_orders(
        prices=(49_504.9, 49_014.7, 48_529.4, 48_048.9, 47_573.1),
        volumes=(0.00202, 0.0020402, 0.0020606, 0.00208121, 0.00210202),
        sides=("buy", "buy", "buy", "buy", "buy"),
    )

    # ==========================================================================
    # 2. SHIFTING UP BUY ORDERS
    await tm.trigger_shift_up_buy_orders(
        new_price=60_000.0,
        prices=(59_405.9, 58_817.7, 58_235.3, 57_658.7, 57_087.8),
        volumes=(0.00168333, 0.00170016, 0.00171717, 0.00173434, 0.00175168),
        sides=("buy", "buy", "buy", "buy", "buy"),
    )
    # ==========================================================================
    # 3. FILLING A BUY ORDER
    # Now lets let the price drop a bit so that a buy order gets triggered.
    await tm.trigger_fill_buy_order(
        no_trigger_price=59_990.0,
        new_price=59_000.0,
        old_prices=(59_405.9, 58_817.7, 58_235.3, 57_658.7, 57_087.8),
        old_volumes=(0.00168333, 0.00170016, 0.00171717, 0.00173434, 0.00175168),
        old_sides=("buy", "buy", "buy", "buy", "buy"),
        new_prices=(58_817.7, 58_235.3, 57_658.7, 57_087.8),
        new_volumes=(0.00170016, 0.00171717, 0.00173434, 0.00175168),
        new_sides=("buy", "buy", "buy", "buy"),
    )

    # ==========================================================================
    # 4. ENSURING N OPEN BUY ORDERS
    await tm.trigger_ensure_n_open_buy_orders(
        new_price=59_100.0,
        prices=(58_817.7, 58_235.3, 57_658.7, 57_087.8, 56_522.5),
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
        prices=(49_603.9, 49_112.7, 48_626.4, 48_144.9, 47_668.2),
        volumes=(0.00201597, 0.00203613, 0.00205649, 0.00207706, 0.00209783),
        sides=("buy", "buy", "buy", "buy", "buy"),
    )

    # ==========================================================================
    # 7. MAX INVESTMENT REACHED
    await tm.check_max_investment_reached(
        current_price=50_000.0,
        n_open_sell_orders=0,
        max_investment=50.0,
    )
