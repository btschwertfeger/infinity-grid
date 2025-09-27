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

from infinity_grid.models.configuration import (
    BotConfigDTO,
    DBConfigDTO,
    NotificationConfigDTO,
)

from .helper import KrakenTestManager
from .kraken_exchange_api import KrakenExchangeAPIConfig

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
        max_investment=10_000.0,
        amount_per_grid=100.0,
        interval=0.01,
        n_open_buy_orders=5,
        verbosity=0,
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
    kraken_config_xbtusd: KrakenExchangeAPIConfig,
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

    tm = KrakenTestManager(
        bot_config=kraken_gridsell_bot_config,
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
    await tm.trigger_fill_buy_order(
        no_trigger_price=59_990.0,
        new_price=59_000.0,
        old_prices=(59_405.9, 58_817.7, 58_235.3, 57_658.7, 57_087.8),
        old_volumes=(0.00168333, 0.00170016, 0.00171717, 0.00173434, 0.00175168),
        old_sides=("buy", "buy", "buy", "buy", "buy"),
        new_prices=(58_817.7, 58_235.3, 57_658.7, 57_087.8, 59_999.9),
        new_volumes=(0.00170016, 0.00171717, 0.00173434, 0.00175168, 0.00168333),
        new_sides=("buy", "buy", "buy", "buy", "sell"),
    )

    # ==========================================================================
    # 4. ENSURING N OPEN BUY ORDERS
    await tm.trigger_ensure_n_open_buy_orders(
        new_price=59_100.0,
        prices=(58_817.7, 58_235.3, 57_658.7, 57_087.8, 59_999.9, 56_522.5),
        volumes=(0.00170016, 0.00171717, 0.00173434, 0.00175168, 0.00168333, 0.0017692),
        sides=("buy", "buy", "buy", "buy", "sell", "buy"),
    )

    # ==========================================================================
    # 5. FILLING A SELL ORDER
    await tm.trigger_fill_sell_order(
        new_price=60_000.0,
        prices=(58_817.7, 58_235.3, 57_658.7, 57_087.8, 56_522.5),
        volumes=(0.00170016, 0.00171717, 0.00173434, 0.00175168, 0.0017692),
        sides=("buy", "buy", "buy", "buy", "buy"),
    )

    # ... as we can see, the sell order got removed from the orderbook.
    # ... there is no new corresponding buy order placed - this would only be
    # the case for the case, if there would be more sell orders.
    # As usual, if the price would rise higher, the buy orders would shift up.

    # ==========================================================================
    # 6. RAPID PRICE DROP - FILLING ALL BUY ORDERS
    await tm.trigger_rapid_price_drop(
        new_price=50_000.0,
        prices=(59_405.8, 58_817.6, 58_235.2, 57_658.6, 57_087.7),
        volumes=(0.00170016, 0.00171717, 0.00173434, 0.00175168, 0.0017692),
        sides=("sell", "sell", "sell", "sell", "sell"),
    )
    # ==========================================================================
    # 7. SELL ALL AND ENSURE N OPEN BUY ORDERS
    await tm.trigger_all_sell_orders(
        new_price=59_100.0,
        buy_prices=(58_514.8, 57_935.4, 57_361.7, 56_793.7, 56_231.3),
        sell_prices=(59_405.8,),
        buy_volumes=(0.00170896, 0.00172606, 0.00174332, 0.00176075, 0.00177836),
        sell_volumes=(0.00170016,),
    )

    # ==========================================================================
    # 8. MAX INVESTMENT REACHED
    await tm.check_max_investment_reached(
        current_price=50_000.0,
        n_open_sell_orders=1,
        max_investment=102.0,
    )

    # ==========================================================================
    # 9. Test what happens if there are not enough funds to place a sell order
    #    for some reason. The GridSell strategy will fail in this case to trigger
    #    a restart (handled by external process manager)
    # Ensure buy orders exist
    tm.check_not_enough_funds_for_sell(
        sell_price=50_500.0,
        n_orders=6,
        n_sell_orders=1,
        fail=True,
        caplog=caplog,
    )


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
    kraken_config_xbtusd: KrakenExchangeAPIConfig,
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

    tm = KrakenTestManager(
        bot_config=kraken_gridsell_bot_config,
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
    assert balances[kraken_config_xbtusd.base_currency]["balance"] == "100.002"
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
