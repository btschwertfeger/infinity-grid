# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Kraken Exchange Adapter for the Infinity Grid Trading Bot.

This module implements adapters for the Kraken exchange REST and WebSocket APIs
that conform to the bot's exchange interface requirements. It provides
functionality for trading operations, account management, and real-time market
data.

The module contains two main adapter classes:
- KrakenExchangeRESTServiceAdapter: Handles all REST API operations like order
    management, balance queries, and exchange status checks.
- KrakenExchangeWebsocketServiceAdapter: Manages WebSocket connections for
    real-time market data and order execution updates.

These adapters translate between the Kraken API's specific implementation
details and the bot's standardized interfaces, ensuring compatibility with the
bot's state machine and event system.

Dependencies:
- kraken-python-sdk: For communication with Kraken API

"""

from contextlib import suppress
from decimal import Decimal
from functools import cached_property, lru_cache
from logging import getLogger
from time import sleep
from typing import Any, Self

try:
    from kraken.exceptions import (
        KrakenAuthenticationError,
        KrakenInvalidOrderError,
        KrakenPermissionDeniedError,
        KrakenUnknownOrderError,
    )
    from kraken.spot import Market, SpotWSClient, Trade, User

except ImportError as exc:
    raise ImportError(
        "The Kraken exchange adapter requires the 'kraken' extra. "
        "Please install it using 'pip install infinity-grid[kraken]'.",
    ) from exc

from infinity_grid.core.event_bus import EventBus
from infinity_grid.core.state_machine import StateMachine, States
from infinity_grid.exceptions import BotStateError, UnknownOrderError
from infinity_grid.interfaces.exchange import (
    IExchangeRESTService,
    IExchangeWebSocketService,
)
from infinity_grid.models.exchange import (
    AssetBalanceSchema,
    AssetPairInfoSchema,
    CreateOrderResponseSchema,
    ExchangeDomain,
    ExecutionsUpdateSchema,
    OnMessageSchema,
    OrderInfoSchema,
    PairBalanceSchema,
    TickerUpdateSchema,
)

LOG = getLogger(__name__)


class KrakenExchangeRESTServiceAdapter(IExchangeRESTService):
    """Adapter for the Kraken exchange user service implementation."""

    def __init__(
        self: Self,
        api_public_key: str,
        api_secret_key: str,
        state_machine: StateMachine,
        base_currency: str,
        quote_currency: str,
    ) -> None:
        self.__base_currency = base_currency
        self.__quote_currency = quote_currency
        self.__user_service: User = User(key=api_public_key, secret=api_secret_key)
        self.__trade_service: Trade = Trade(key=api_public_key, secret=api_secret_key)
        self.__market_service: Market = Market()
        self.__state_machine: StateMachine = state_machine

    # == Implemented abstract methods from IExchangeRESTService ================

    def check_api_key_permissions(self: Self) -> None:
        """
        Checks if the credentials are valid and if the API keys have the
        required permissions.
        """
        try:
            LOG.info("- Checking permissions of API keys...")

            LOG.info(" - Checking if 'Query Funds' permission set...")
            self.__user_service.get_account_balance()

            LOG.info(" - Checking if 'Query open order & trades' permission set...")
            self.__user_service.get_open_orders(trades=True)

            LOG.info(" - Checking if 'Query closed order & trades' permission set...")
            self.__user_service.get_closed_orders(trades=True)

            LOG.info(" - Checking if 'Create & modify orders' permission set...")
            self.__trade_service.create_order(
                pair="BTC/USD",
                side="buy",
                ordertype="market",
                volume="10",
                price="10",
                validate=True,
            )
            LOG.info(" - Checking if 'Cancel & close orders' permission set...")
            with suppress(KrakenInvalidOrderError):
                self.__trade_service.cancel_order(
                    txid="",
                    extra_params={"cl_ord_id": "infinity_grid_internal"},
                )

            LOG.info(" - Checking if 'Websocket interface' permission set...")
            self.__user_service.request(
                method="POST",
                uri="/0/private/GetWebSocketsToken",
            )

            LOG.info(" - Passed API keys and permissions are valid!")
        except (KrakenAuthenticationError, KrakenPermissionDeniedError) as exc:
            self.__state_machine.transition_to(States.ERROR)
            message = (
                "Passed API keys are invalid!"
                if isinstance(exc, KrakenAuthenticationError)
                else "Passed API keys are missing permissions!"
            )
            raise BotStateError(message) from exc

    def check_exchange_status(self: Self, tries: int = 0) -> None:
        """Checks whether the Kraken API is available."""
        if tries == 3:
            LOG.error("- Could not connect to the Kraken Exchange API.")
            self.__state_machine.transition_to(States.ERROR)
            raise BotStateError(
                "Could not connect to the Kraken Exchange API after 3 tries.",
            )
        try:
            if (
                status := self.__market_service.get_system_status()
                .get("status", "")
                .lower()
            ) == "online":
                LOG.info("- Kraken Exchange API Status: Online")
                return
            LOG.warning("- Kraken Exchange API Status: %s", status)
            raise ConnectionError("Kraken API is not online.")
        except (
            Exception  # noqa: BLE001
        ) as exc:  # pylint: disable=broad-exception-caught
            LOG.debug(
                "Exception while checking Kraken API status: %s",
                exc,
                exc_info=exc,
            )
            LOG.warning("- Kraken not available. (Try %d/3)", tries + 1)
            sleep(3)
            self.check_exchange_status(tries=tries + 1)

    def get_orders_info(self: Self, txid: str) -> OrderInfoSchema | None:
        """
        Return the order information for a given transaction ID (txid) from the
        upstream.
        """
        if not (order_info := self.__user_service.get_orders_info(txid=txid).get(txid)):
            return None

        return OrderInfoSchema(
            pair=order_info["descr"]["pair"],
            price=order_info["descr"]["price"],
            side=order_info["descr"]["type"],
            status=order_info["status"],
            txid=txid,
            userref=order_info["userref"],
            vol_exec=order_info["vol_exec"],
            vol=order_info["vol"],
        )

    def get_open_orders(
        self: Self,
        userref: int,
        trades: bool = False,
    ) -> list[OrderInfoSchema]:
        orders = []
        for txid, order in self.__user_service.get_open_orders(
            userref=userref,
            trades=trades,
        )["open"].items():
            orders.append(
                OrderInfoSchema(
                    pair=order["descr"]["pair"],
                    price=order["descr"]["price"],
                    side=order["descr"]["type"],
                    status=order["status"],
                    txid=txid,
                    userref=order["userref"],
                    vol_exec=order["vol_exec"],
                    vol=order["vol"],
                ),
            )
        return orders

    def get_order_with_retry(
        self: Self,
        txid: str,
        tries: int = 0,
        max_tries: int = 5,
        exit_on_fail: bool = True,
    ) -> OrderInfoSchema:
        """
        Returns the order details for a given txid.

        NOTE: We need retry here, since Kraken lacks of fast processing of
              placed/filled orders and making them available via REST API.
        """
        while tries < max_tries and not (
            order_details := self.get_orders_info(txid=txid)
        ):
            tries += 1
            LOG.warning(
                "Could not find order '%s'. Retry %d/%d in %d seconds...",
                txid,
                tries,
                max_tries,
                (wait_time := 2 * tries),
            )
            sleep(wait_time)

        if exit_on_fail and order_details is None:
            message = (
                f"Failed to retrieve order info for '{txid}' after {max_tries} retries!"
            )
            LOG.error(message)
            self.__state_machine.transition_to(States.ERROR)
            raise BotStateError(message)

        return order_details

    def get_account_balance(self: Self) -> dict[str, float]:
        """
        Function only used to check the API key permissions during
        initialization.
        """
        return self.__user_service.get_account_balance()  # type: ignore[no-any-return]

    def get_closed_orders(
        self: Self,
        userref: int | None = None,
        trades: bool | None = None,
    ) -> dict[str, Any]:
        """
        Function only used to check the API key permissions during
        initialization.
        """
        return self.__user_service.get_closed_orders(userref=userref, trades=trades)  # type: ignore[no-any-return]

    def get_balances(self: Self) -> list[AssetBalanceSchema]:
        """Retrieve the user's balances"""
        LOG.debug("Retrieving the user's balances...")
        balances = []
        for symbol, data in self.__user_service.get_balances().items():
            balances.append(AssetBalanceSchema(asset=symbol, **data))
        return balances

    def get_pair_balance(
        self: Self,
    ) -> PairBalanceSchema:
        """
        Returns the available and overall balances of the quote and base
        currency.

        FIXME: Is there a way to get the balances of the asset pair directly?
        FIXME: Respect balances held by auto earn
        """
        custom_base, custom_quote = self.__retrieve_custom_base_quote_names()

        base_balance = Decimal(0)
        base_available = Decimal(0)
        quote_balance = Decimal(0)
        quote_available = Decimal(0)

        for balance in self.get_balances():
            if balance.asset == custom_base:
                base_balance = Decimal(balance.balance)
                base_available = base_balance - Decimal(balance.hold_trade)
            elif balance.asset == custom_quote:
                quote_balance = Decimal(balance.balance)
                quote_available = quote_balance - Decimal(balance.hold_trade)

        LOG.debug(
            "Retrieved balances: %s",
            balances := PairBalanceSchema(
                base_balance=float(base_balance),
                quote_balance=float(quote_balance),
                base_available=float(base_available),
                quote_available=float(quote_available),
            ),
        )
        return balances

    @cached_property
    def ws_symbol(self: Self) -> str:
        """Returns the symbol for the given base and quote currency."""
        return f"{self.__base_currency}/{self.__quote_currency}"

    @cached_property
    def ws_altname(self: Self) -> str:
        base_currency, quote_currency = self.rest_symbol.split("/")
        return f"{base_currency}{quote_currency}"

    @cached_property
    def rest_symbol(self: Self) -> str:
        """Returns the symbol for the given base and quote currency."""
        asset_response = self.__market_service.get_assets(
            assets=[self.__base_currency, self.__quote_currency],
        )

        base_currency = quote_currency = None
        assets = {self.__base_currency, self.__quote_currency}
        for key, value in asset_response.items():
            if key.startswith("Z") and key[1:] in assets:
                # The Kraken exchange is inconsistent in terms of return values.
                # When BTC is the base and EUR the quote currency, the altnames
                # will be BTC and EUR, while the asset pair AVAX/EUR or DOT/EUR
                # will return AVAX and ZEUR or DOT ZEUR. So we need to cut of
                # the Z in case.
                key = key[1:]  # noqa: PLW2901

            if key == self.__base_currency:
                base_currency = value["altname"]
            elif key == self.__quote_currency:
                quote_currency = value["altname"]

        if not base_currency or not quote_currency:
            self.__state_machine.transition_to(States.ERROR)
            raise BotStateError(
                f"Could not find altname for base '{self.__base_currency}' or"
                f" quote '{self.__quote_currency}' currency.",
            )
        return f"{base_currency}/{quote_currency}"

    @cached_property
    def rest_altname(self: Self) -> str:
        base_currency, quote_currency = self.rest_symbol.split("/")
        return f"{base_currency}{quote_currency}"

    def create_order(
        self: Self,
        *,
        ordertype: str,
        side: str,
        volume: float,
        price: float,
        userref: int,
        validate: bool = False,
        oflags: str | None = None,
    ) -> CreateOrderResponseSchema:
        """Create a new order."""
        return CreateOrderResponseSchema(
            txid=self.__trade_service.create_order(
                ordertype=ordertype,
                side=side,
                volume=volume,
                pair=self.rest_altname,
                price=price,
                userref=userref,
                validate=validate,
                oflags=oflags,
            )["txid"][0],
        )

    def cancel_order(self: Self, txid: str, **kwargs: dict[str, Any]) -> None:
        """Cancel an order."""
        try:
            self.__trade_service.cancel_order(txid=txid, **kwargs)
        except KrakenUnknownOrderError as exc:
            raise UnknownOrderError from exc

    def truncate(
        self: Self,
        amount: float | Decimal | str,
        amount_type: str,
    ) -> str:
        """Truncate amount according to exchange precision."""
        return self.__trade_service.truncate(  # type: ignore[no-any-return]
            amount=amount,
            amount_type=amount_type,
            pair=self.rest_altname,
        )

    def get_system_status(self: Self) -> str:
        """Get the current system status of the exchange."""
        return self.__market_service.get_system_status()["status"]  # type: ignore[no-any-return]

    def get_asset_pair_info(
        self: Self,
    ) -> AssetPairInfoSchema:
        """Get available asset pair information from the exchange."""
        # NOTE: Kraken allows "XBTUSD", "BTCUSD", "BTC/USD" but not "XBT/USD"
        # which is the actual self.rest_symbol, so we need to use self.ws_symbol
        # here. Ticket Nr.: 18252552
        if (
            pair_info := self.__market_service.get_asset_pairs(pair=self.ws_symbol)
        ) == {}:
            self.__state_machine.transition_to(States.ERROR)
            raise BotStateError(
                f"Could not get asset pair info for {self.rest_symbol}."
                " Please check the pair name and try again.",
            )
        return AssetPairInfoSchema(**pair_info[next(iter(pair_info))])

    @lru_cache(maxsize=1)  # noqa: B019
    def get_exchange_domain(self) -> ExchangeDomain:
        return ExchangeDomain(
            EXCHANGE="Kraken",
            BUY="buy",
            SELL="sell",
            OPEN="open",
            CLOSED="closed",
            CANCELED="canceled",
            EXPIRED="expired",
            PENDING="pending",
        )

    # == Custom Kraken Methods for convenience =================================

    @lru_cache(maxsize=1)  # noqa: B019
    def __retrieve_custom_base_quote_names(self: Self) -> tuple[str, str]:
        """
        Returns the custom base and quote name for the given currencies.
        On Kraken, crypto assets are prefixed with 'X' (e.g., 'XETH', 'XXBT'),
        while fiat assets are prefixed with 'Z' (e.g., 'ZEUR', 'ZUSD').

        This can be cached, since the asset names do not change frequently.
        """
        pair_info: AssetPairInfoSchema = self.get_asset_pair_info()
        return pair_info.base, pair_info.quote


class KrakenExchangeWebsocketServiceAdapter(IExchangeWebSocketService):
    """Adapter for the Kraken exchange websocket service implementation."""

    def __init__(
        self: Self,
        api_public_key: str,
        api_secret_key: str,
        state_machine: StateMachine,
        event_bus: EventBus,
    ) -> None:
        self.__websocket_service: SpotWSClient = SpotWSClient(
            key=api_public_key,
            secret=api_secret_key,
            callback=self.on_message,
        )
        self.__state_machine: StateMachine = state_machine
        self.__event_bus: EventBus = event_bus

    async def start(self: Self) -> None:
        """Start the websocket service."""
        await self.__websocket_service.start()

    async def close(self: Self) -> None:
        """Cancel the websocket service."""
        await self.__websocket_service.close()

    async def subscribe(self: Self, params: dict[str, Any]) -> None:
        """Subscribe to the websocket service."""
        await self.__websocket_service.subscribe(params=params)

    async def on_message(self: Self, message: dict) -> None:
        """Handle incoming messages from the WebSocket."""

        if self.__state_machine.state in {States.SHUTDOWN_REQUESTED, States.ERROR}:
            LOG.debug("Shutdown requested, not processing incoming messages.")
            return

        # Filtering out unwanted messages
        if not isinstance(message, dict):
            LOG.warning("Message is not a dict: %s", message)  # type: ignore[unreachable]
            return

        if (channel := message.get("channel")) in {
            "heartbeat",
            "status",
            "pong",
        } or message.get("python-kraken-sdk"):
            return

        if method := message.get("method"):
            if method == "subscribe" and not message["success"]:
                LOG.error(
                    "The algorithm was not able to subscribe to selected channels!",
                )
                self.__state_machine.transition_to(States.ERROR)
                return
            return

        if not channel:
            LOG.warning("Message has no channel: %s", message)
            return

        new_message = OnMessageSchema(
            channel=channel,
            type=message.get("type"),  # "update", "snapshot" or None
        )

        if channel == "ticker":
            new_message.ticker_data = TickerUpdateSchema(**message["data"][0])
        elif channel == "executions":
            new_message.executions = [
                ExecutionsUpdateSchema(
                    order_id=execution["order_id"],
                    exec_type=execution["exec_type"],
                )
                for execution in message["data"]
            ]

        self.__event_bus.publish("on_message", data=new_message)
