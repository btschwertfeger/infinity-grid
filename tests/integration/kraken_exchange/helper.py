# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

import logging
from collections.abc import Iterable
from typing import Self

from infinity_grid.core.engine import BotEngine
from infinity_grid.core.state_machine import States
from infinity_grid.models.configuration import (
    BotConfigDTO,
    DBConfigDTO,
    NotificationConfigDTO,
)

from .kraken_exchange_api import KrakenAPI, KrakenExchangeAPIConfig

LOG = logging.getLogger(__name__)


async def get_kraken_instance(
    bot_config: BotConfigDTO,
    db_config: DBConfigDTO,
    notification_config: NotificationConfigDTO,
    kraken_config: KrakenExchangeAPIConfig,
) -> BotEngine:
    """
    Initialize the Bot Engine using the passed config strategy and Kraken backend

    The Kraken API is mocked to avoid creating, modifying, or canceling real
    orders.
    """
    engine = BotEngine(
        bot_config=bot_config,
        db_config=db_config,
        notification_config=notification_config,
    )

    from infinity_grid.adapters.exchanges.kraken import (
        KrakenExchangeRESTServiceAdapter,
        KrakenExchangeWebsocketServiceAdapter,
    )

    # ==========================================================================
    # Initialize the mocked REST API client
    engine._BotEngine__strategy._rest_api = KrakenExchangeRESTServiceAdapter(
        api_public_key=bot_config.api_public_key,
        api_secret_key=bot_config.api_secret_key,
        state_machine=engine._BotEngine__state_machine,
        base_currency=bot_config.base_currency,
        quote_currency=bot_config.quote_currency,
    )

    api = KrakenAPI(kraken_config)
    engine._BotEngine__strategy._rest_api._KrakenExchangeRESTServiceAdapter__user_service = (
        api
    )
    engine._BotEngine__strategy._rest_api._KrakenExchangeRESTServiceAdapter__trade_service = (
        api
    )
    engine._BotEngine__strategy._rest_api._KrakenExchangeRESTServiceAdapter__market_service = (
        api
    )

    # ==========================================================================
    # Initialize the websocket client
    engine._BotEngine__strategy._GridHODLStrategy__ws_client = (
        KrakenExchangeWebsocketServiceAdapter(
            api_public_key=bot_config.api_public_key,
            api_secret_key=bot_config.api_secret_key,
            state_machine=engine._BotEngine__state_machine,
            event_bus=engine._BotEngine__event_bus,
        )
    )
    # Stop the connection directly
    await engine._BotEngine__strategy._GridHODLStrategy__ws_client.close()
    # Use the mocked API client
    engine._BotEngine__strategy._GridHODLStrategy__ws_client.__websocket_service = api

    # ==========================================================================
    # Misc
    engine._BotEngine__strategy._exchange_domain = (
        engine._BotEngine__strategy._rest_api.get_exchange_domain()
    )

    return engine, api


class KrakenTestManager:

    def __init__(
        self: Self,
        bot_config: BotConfigDTO,
        notification_config: NotificationConfigDTO,
        db_config: DBConfigDTO,
        kraken_config: KrakenExchangeAPIConfig,
    ) -> None:
        self.__bot_config = bot_config
        self.__notification_config = notification_config
        self.__db_config = db_config
        self.__kraken_config = kraken_config
        self.__engine = None
        self.__api = None  # the mocked KrakenAPI instance

    # --------------------------------------------------------------------------
    async def initialize_engine(self: Self) -> None:
        self.__engine, self.__api = await get_kraken_instance(
            bot_config=self.__bot_config,
            notification_config=self.__notification_config,
            db_config=self.__db_config,
            kraken_config=self.__kraken_config,
        )

    # --------------------------------------------------------------------------

    async def trigger_prepare_for_trading(
        self: Self,
        initial_ticker: float,
    ) -> None:
        LOG.info("******* Trigger prepare for trading *******")
        await self.ws_client.on_message(
            {
                "channel": "executions",
                "type": "snapshot",
                "data": [{"exec_type": "canceled", "order_id": "txid0"}],
            },
        )
        assert self.state_machine.state == States.INITIALIZING
        assert self.strategy._ready_to_trade is False

        await self.api.on_ticker_update(
            callback=self.ws_client.on_message,
            last=initial_ticker,
        )
        assert self.strategy._ticker == initial_ticker
        assert self.state_machine.state == States.RUNNING
        assert self.strategy._ready_to_trade is True

    async def check_initial_n_buy_orders(
        self: Self,
        prices: tuple[float],
        volumes: tuple[float],
        sides: tuple[str] = ("buy", "buy", "buy", "buy", "buy"),
    ) -> None:
        # 1. PLACEMENT OF INITIAL N BUY ORDERS
        # After both fake-websocket channels are connected, the algorithm went
        # through its full setup and placed orders against the fake Kraken API and
        # finally saved those results into the local orderbook table.

        # Check if the five initial buy orders are placed with the expected price
        # and volume. Note that the interval is not exact due to the fee
        # which is taken into account.
        LOG.info("******* Check initial n buy orders *******")
        self.__ensure_orders_correct(prices, volumes, sides)

    async def trigger_shift_up_buy_orders(
        self: Self,
        new_price: float,
        prices: tuple[float],
        volumes: tuple[float],
    ) -> None:
        # 2. SHIFTING UP BUY ORDERS
        # Check if shifting up the buy orders works
        LOG.info("******* Check shifting up buy orders works *******")
        await self.api.on_ticker_update(
            callback=self.ws_client.on_message,
            last=new_price,
        )
        assert self.strategy._ticker == new_price
        assert self.state_machine.state == States.RUNNING

        # We should now still have 5 buy orders, but at a higher price. The
        # other orders should be canceled.
        for order, price, volume in zip(
            self.strategy._orderbook_table.get_orders().all(),
            prices,
            volumes,
            strict=True,
        ):
            assert order.price == price
            assert order.volume == volume
            assert order.side == "buy"
            assert order.symbol == self.__kraken_config.pair
            assert order.userref == self.strategy._config.userref

    async def trigger_fill_buy_order(
        self: Self,
        no_trigger_price: float,
        new_price: float,
        old_prices: tuple[float],
        old_volumes: tuple[float],
        old_sides: tuple[str],
        new_prices: tuple[float],
        new_volumes: tuple[float],
        new_sides: tuple[str],
    ) -> None:
        LOG.info("******* Check filling a buy order works *******")
        # 3. FILLING A BUY ORDER
        # Now lets let the price drop a bit, just to check if nothing happens.
        await self.api.on_ticker_update(
            callback=self.ws_client.on_message,
            last=no_trigger_price,
        )
        assert self.state_machine.state == States.RUNNING
        assert self.strategy._ticker == no_trigger_price

        # Quick re-check ... the price update should not affect any orderbook
        # changes when dropping.
        self.__ensure_orders_correct(old_prices, old_volumes, old_sides)

        # Now trigger the execution of the first buy order
        await self.api.on_ticker_update(
            callback=self.ws_client.on_message,
            last=new_price,
        )
        assert self.state_machine.state == States.RUNNING
        assert self.strategy._ticker == new_price

        # Ensure that we have a filled order and possibly a new sell order
        self.__ensure_orders_correct(new_prices, new_volumes, new_sides)

    async def trigger_ensure_n_open_buy_orders(
        self: Self,
        new_price: float,
        prices: tuple[float],
        volumes: tuple[float],
        sides: tuple[str],
    ) -> None:
        LOG.info("******* Check ensuring N open buy orders *******")
        await self.api.on_ticker_update(
            callback=self.ws_client.on_message,
            last=new_price,
        )
        assert self.state_machine.state == States.RUNNING
        assert self.strategy._ticker == new_price
        self.__ensure_orders_correct(prices, volumes, sides)

    async def trigger_rapid_price_drop(
        self: Self,
        new_price: float,
        prices: tuple[float],
        volumes: tuple[float],
        sides: tuple[str],
    ) -> None:
        # 5. RAPID PRICE DROP - FILLING ALL BUY ORDERS
        LOG.info("******* Check rapid price drop - filling all buy orders *******")

        await self.api.on_ticker_update(
            callback=self.ws_client.on_message,
            last=new_price,
        )
        assert self.state_machine.state == States.RUNNING
        assert self.strategy._ticker == new_price
        self.__ensure_orders_correct(prices, volumes, sides)

    async def trigger_fill_sell_order(
        self: Self,
        new_price: float,
        prices: tuple[float],
        volumes: tuple[float],
        sides: tuple[str],
    ) -> None:
        LOG.info("******* Filling a sell order *******")
        await self.api.on_ticker_update(
            callback=self.ws_client.on_message,
            last=new_price,
        )
        assert self.state_machine.state == States.RUNNING
        assert self.strategy._ticker == new_price
        self.__ensure_orders_correct(prices, volumes, sides)

    async def trigger_all_sell_orders(
        self: Self,
        new_price: float,
        buy_prices: tuple[float],
        sell_prices: tuple[float],
        buy_volumes: tuple[float],
        sell_volumes: tuple[float],
    ) -> None:
        # FIXME: is that true?:
        #    Here we temporarily have more than 5 buy orders, since every sell
        #    order triggers a new buy order, causing us to have 9 buy orders and
        #    a single sell order. Which is not a problem, since the buy orders
        #    that are too much will get canceled after the next price update.
        LOG.info("******* Filling all sell orders *******")

        await self.api.on_ticker_update(
            callback=self.ws_client.on_message,
            last=new_price,
        )
        assert self.state_machine.state == States.RUNNING
        current_orders = self.strategy._orderbook_table.get_orders().all()

        self.__ensure_orders_correct(
            sell_prices,
            sell_volumes,
            ("sell",),
            (o for o in current_orders if o.side == "sell"),
        )
        self.__ensure_orders_correct(
            buy_prices,
            buy_volumes,
            (
                "buy",
                "buy",
                "buy",
                "buy",
                "buy",
            ),
            (o for o in current_orders if o.side == "buy"),
        )

    # --------------------------------------------------------------------------
    def __ensure_orders_correct(
        self: Self,
        prices: tuple[float],
        volumes: tuple[float],
        sides: tuple[str],
        orders: Iterable | None = None,
    ) -> None:
        for order, price, volume, side in zip(
            orders or self.strategy._orderbook_table.get_orders().all(),
            prices,
            volumes,
            sides,
            strict=True,
        ):
            assert order.price == price
            assert order.volume == volume
            assert order.side == side
            assert order.symbol == self.__kraken_config.pair
            assert order.userref == self.strategy._config.userref

    # --------------------------------------------------------------------------
    # Properties
    @property
    def engine(self: Self) -> Self:
        if self.__engine is None:
            raise ValueError("Engine not initialized. Call 'initialize_engine' first.")
        return self.__engine

    @property
    def state_machine(self: Self) -> Self:
        return self.engine._BotEngine__state_machine

    @property
    def strategy(self: Self) -> Self:
        return self.engine._BotEngine__strategy

    @property
    def ws_client(self: Self) -> Self:
        return self.strategy._GridHODLStrategy__ws_client

    @property
    def rest_api(self: Self) -> Self:
        return self.strategy._rest_api

    @property
    def api(self: Self) -> Self:
        return self.__api
