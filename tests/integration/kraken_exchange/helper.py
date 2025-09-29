# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

import logging
from collections.abc import Iterable
from typing import Self
from unittest import mock

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
    """
    Helper class to manage the Kraken integration tests

    It provides methods to initialize the engine and helper functions to trigger
    certain actions and check the results.

    Functions are numbered like '# 0., # 1., # 2., ...' to indicate the order
    in which they should be called. Functions without numbers are helper
    functions that can be called at any time (if needed).

    NOTE: Some functions are redundant. This is intentional to have speaking
          names, even if they do the same as another function.
    """

    def __init__(
        self: Self,
        bot_config: BotConfigDTO,
        notification_config: NotificationConfigDTO,
        db_config: DBConfigDTO,
        kraken_config: KrakenExchangeAPIConfig,
    ) -> None:
        self.bot_config = bot_config
        self.exchange_config = kraken_config
        self.__notification_config = notification_config
        self.__db_config = db_config
        self.__engine = None
        self.__api = None  # the mocked KrakenAPI instance

    # --------------------------------------------------------------------------

    async def initialize_engine(self: Self) -> None:
        """
        Initialize the BotEngine, must be called before using other methods.
        """
        self.__engine, self.__api = await get_kraken_instance(
            bot_config=self.bot_config,
            notification_config=self.__notification_config,
            db_config=self.__db_config,
            kraken_config=self.exchange_config,
        )

    # --------------------------------------------------------------------------

    async def trigger_prepare_for_trading(
        self: Self,
        initial_ticker: float,
    ) -> None:
        """
        # 0. PREPARE FOR TRADING

        Initiates the bot initialization phase that is characterized by
        connecting to the dummy websocket channels as well as setting the
        algorithm to the running state.
        """
        LOG.info("******* Trigger prepare for trading *******")
        await self.ws_client.on_message(
            {
                "channel": "executions",
                "type": "snapshot",
                "data": [{"exec_type": "canceled", "order_id": "txid0"}],
            },
        )
        assert (
            self.state_machine.state == States.INITIALIZING
        ), f"Expected state INITIALIZING, got {self.state_machine.state}"
        assert (
            self.strategy._ready_to_trade is False
        ), f"Expected _ready_to_trade False, got {self.strategy._ready_to_trade}"

        await self.api.on_ticker_update(
            callback=self.ws_client.on_message,
            last=initial_ticker,
        )
        assert (
            self.strategy._ticker == initial_ticker
        ), f"Expected ticker {initial_ticker}, got {self.strategy._ticker}"
        assert (
            self.state_machine.state == States.RUNNING
        ), f"Expected state RUNNING, got {self.state_machine.state}"
        assert self.strategy._ready_to_trade is True

    async def check_initial_n_buy_orders(
        self: Self,
        prices: tuple[float],
        volumes: tuple[float],
        sides: tuple[str],
    ) -> None:
        """
        # 1. PLACEMENT OF INITIAL N BUY ORDERS

        Function that must be executed first, right after the bot has been
        initialized and is in running state.

        This places the initial n buy orders and checks if they are correct.

        After both fake-websocket channels are connected, the algorithm went
        through its full setup and placed orders against the fake Kraken API and
        finally saved those results into the local orderbook table.

        - Check if the five initial buy orders are placed with the expected
          price and volume.
        - Note that the interval is not exact due to the fee which is taken into
          account.
        """
        LOG.info("******* Check initial n buy orders *******")
        self.__ensure_orders_correct(prices, volumes, sides)

    async def trigger_shift_up_buy_orders(
        self: Self,
        new_price: float,
        prices: tuple[float],
        volumes: tuple[float],
        sides: tuple[str],
    ) -> None:
        """
        # 2. SHIFTING UP BUY ORDERS

        Function to check if shifting up the buy orders works.
        """
        LOG.info("******* Check shifting up buy orders works *******")
        await self.__price_change_order_check(new_price, prices, volumes, sides)

    async def trigger_ensure_n_open_buy_orders(
        self: Self,
        new_price: float,
        prices: tuple[float],
        volumes: tuple[float],
        sides: tuple[str],
    ) -> None:
        """
        # TRIGGER ENSURE N OPEN BUY ORDERS

        Function to trigger and check the placement of n open buy orders.
        """
        LOG.info("******* Check ensuring n open buy orders *******")
        await self.__price_change_order_check(new_price, prices, volumes, sides)

    async def trigger_rapid_price_drop(
        self: Self,
        new_price: float,
        prices: tuple[float],
        volumes: tuple[float],
        sides: tuple[str],
    ) -> None:
        """
        # RAPID PRICE DROP - FILLING ALL BUY ORDERS

        Function to check the behavior for a rapid price drop that fills all buy
        orders.

        Depending on the strategy, there are either no open orders after this
        function was executed (e.g. during cDCA) or all buy orders were filled
        and according sell orders were placed (e.g. during GridHODL, GridSell,
        and SWING).
        """
        LOG.info("******* Check rapid price drop - filling all buy orders *******")
        await self.__price_change_order_check(new_price, prices, volumes, sides)

    async def trigger_fill_sell_order(
        self: Self,
        new_price: float,
        prices: tuple[float],
        volumes: tuple[float],
        sides: tuple[str],
    ) -> None:
        """
        # TRIGGER FILLING A SELL ORDER

        Function to check if filling a sell order works.
        """
        LOG.info("******* Filling a sell order *******")
        await self.__price_change_order_check(new_price, prices, volumes, sides)

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
        """
        # FILLING A BUY ORDER

        Function checking if filling a buy order works. It takes old prices,
        volumes, and sides and checks if they are still the same after a price
        update that does not trigger any order. Then it triggers a price update
        that fills a buy order and checks if the new orders are as expected.
        """
        LOG.info("******* Check filling a buy order works *******")
        # Now lets let the price drop a bit, just to check if nothing happens.
        await self.api.on_ticker_update(
            callback=self.ws_client.on_message,
            last=no_trigger_price,
        )
        assert (
            self.state_machine.state == States.RUNNING
        ), f"Expected state RUNNING, got {self.state_machine.state}"
        assert (
            self.strategy._ticker == no_trigger_price
        ), f"Expected ticker {no_trigger_price}, got {self.strategy._ticker}"

        # Quick re-check ... the price update should not affect any orderbook
        # changes when dropping.
        self.__ensure_orders_correct(old_prices, old_volumes, old_sides)

        # Now trigger the execution of the first buy order
        await self.api.on_ticker_update(
            callback=self.ws_client.on_message,
            last=new_price,
        )
        assert (
            self.state_machine.state == States.RUNNING
        ), f"Expected state RUNNING, got {self.state_machine.state}"
        assert (
            self.strategy._ticker == new_price
        ), f"Expected ticker {new_price}, got {self.strategy._ticker}"

        # Ensure that we have a filled order and possibly a new sell order
        self.__ensure_orders_correct(new_prices, new_volumes, new_sides)

    async def trigger_all_sell_orders(
        self: Self,
        new_price: float,
        buy_prices: tuple[float],
        sell_prices: tuple[float],
        buy_volumes: tuple[float],
        sell_volumes: tuple[float],
    ) -> None:
        """
        # FILLING ALL SELL ORDERS

        Function to check if filling all sell orders works.
        """
        # FIXME: this is not triggering all sell orders
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
        assert (
            self.state_machine.state == States.RUNNING
        ), f"Expected state RUNNING, got {self.state_machine.state}"
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

    async def check_not_enough_funds_for_sell(
        self: Self,
        sell_price: float,  # FIXME: naming
        n_orders: int,
        n_sell_orders: int,
        assume_base_available: float,
        assume_quote_available: float,
        fail: bool,
    ) -> None:
        """
        # NOT ENOUGH FUNDS FOR SELL ORDER

        Function that mocks the available balances to check how the algorithm
        behaves when there are not enough funds to place a sell order.

        :param fail: If the algorithm should enter error state, this is the case
            for GridSell, where one must always have enough funds to place the
            sell order.
        :type fail: bool
        """
        LOG.info("******* Check not enough funds for sell order *******")

        # Save the original method to restore it later
        original_get_pair_balance = self.strategy._rest_api.get_pair_balance

        # Mock the instance method directly
        self.rest_api.get_pair_balance = mock.Mock(
            return_value=mock.Mock(
                base_available=assume_base_available,
                quote_available=assume_quote_available,
            ),
        )

        try:
            # Now trigger the sell order
            await self.api.on_ticker_update(
                callback=self.ws_client.on_message,
                last=sell_price,
            )
            assert (
                self.state_machine.state == States.RUNNING if not fail else States.ERROR
            )
            assert (
                self.strategy._orderbook_table.count() == n_orders
            ), f"Expected {n_orders} open orders, got {self.strategy._orderbook_table.count()}"
            assert (
                len(
                    self.strategy._orderbook_table.get_orders(
                        filters={"side": "sell"},
                    ).all(),
                )
                == n_sell_orders
            )
        finally:
            # Restore the original method
            self.engine._BotEngine__strategy._rest_api.get_pair_balance = (
                original_get_pair_balance
            )

    async def check_max_investment_reached(
        self: Self,
        current_price: float,
        n_open_sell_orders: int,
        max_investment: float = 202.0,
    ) -> None:
        """
        # MAX INVESTMENT REACHED

        Function to check the behavior when the max investment is reached.
        """
        LOG.info("******* Check max investment reached *******")

        # First ensure that new buy orders can be placed...
        assert not self.strategy._max_investment_reached
        self.strategy._GridStrategyBase__cancel_all_open_buy_orders()
        assert (
            self.strategy._orderbook_table.count(filters={"side": "buy"}) == 0
        ), f"Expected 0 open buy orders, got {self.strategy._orderbook_table.count(filters={'side': 'buy'})}"
        await self.api.on_ticker_update(
            callback=self.ws_client.on_message,
            last=current_price,
        )
        assert (
            self.strategy._orderbook_table.count()
            == n_open_sell_orders + self.bot_config.n_open_buy_orders
        )

        # Now with a different max investment, the max investment should be
        # reached and no further orders be placed.
        assert not self.strategy._max_investment_reached
        old_max_investment = self.strategy._config.max_investment
        self.strategy._config.max_investment = max_investment
        self.strategy._GridStrategyBase__cancel_all_open_buy_orders()
        assert (
            self.strategy._orderbook_table.count(filters={"side": "buy"}) == 0
        ), f"Expected 0 open buy orders, got {self.strategy._orderbook_table.count(filters={'side': 'buy'})}"
        assert (
            self.strategy._orderbook_table.count(filters={"side": "sell"})
            == n_open_sell_orders
        )
        await self.api.on_ticker_update(
            callback=self.ws_client.on_message,
            last=current_price,
        )
        assert self.strategy._orderbook_table.count(filters={"side": "buy"}) == 0
        assert (
            self.strategy._orderbook_table.count(filters={"side": "sell"})
            == n_open_sell_orders
        )
        assert self.strategy._max_investment_reached, "Max investment should be reached"
        assert (
            self.state_machine.state == States.RUNNING
        ), f"Expected state RUNNING, got {self.state_machine.state}"
        self.strategy._config.max_investment = old_max_investment

    # --------------------------------------------------------------------------

    async def __price_change_order_check(
        self: Self,
        new_price: float,
        prices: tuple[float],
        volumes: tuple[float],
        sides: tuple[str],
        orders: Iterable | None = None,
    ) -> None:
        """
        Update the price and check if the orders are matching the expected ones.
        """
        await self.api.on_ticker_update(
            callback=self.ws_client.on_message,
            last=new_price,
        )
        assert (
            self.strategy._ticker == new_price
        ), f"Expected ticker {new_price}, got {self.strategy._ticker}"
        assert (
            self.state_machine.state == States.RUNNING
        ), f"Expected state RUNNING, got {self.state_machine.state}"
        self.__ensure_orders_correct(prices, volumes, sides, orders)

    def __ensure_orders_correct(
        self: Self,
        prices: tuple[float],
        volumes: tuple[float],
        sides: tuple[str],
        orders: Iterable | None = None,
    ) -> None:
        """
        Check if the current orders are matching the expected ones.
        """
        for order, price, volume, side in zip(
            orders or self.strategy._orderbook_table.get_orders().all(),
            prices,
            volumes,
            sides,
            strict=True,
        ):
            assert order.price == price, f"Expected price {price}, got {order.price}"
            assert (
                order.volume == volume
            ), f"Expected volume {volume}, got {order.volume}"
            assert order.side == side, f"Expected side {side}, got {order.side}"
            assert (
                order.symbol == self.exchange_config.pair
            ), f"Expected symbol {self.exchange_config.pair}, got {order.symbol}"
            assert (
                order.userref == self.strategy._config.userref
            ), f"Expected userref {self.strategy._config.userref}, got {order.userref}"

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
