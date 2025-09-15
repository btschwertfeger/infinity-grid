# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#
# pylint: disable=arguments-differ

"""Helper data structures used for integration testing."""

import uuid
from copy import deepcopy
from typing import Any, Callable, Self

from kraken.spot import Market, Trade, User

from infinity_grid.core.engine import BotEngine
from infinity_grid.models.configuration import (
    BotConfigDTO,
    DBConfigDTO,
    NotificationConfigDTO,
)


class KrakenAPI(Market, Trade, User):
    """
    Class extending the Market, Trade, and User client of the python-kraken-sdk
    to use its methods for non-authenticated requests.

    This class tries to simulate the backend of the Kraken Exchange, handling
    orders and trades used during tests.
    """

    def __init__(self: Self) -> None:
        super().__init__()  # DONT PASS SECRETS!
        self.__orders = {}
        self.__balances = {
            "XXBT": {"balance": "100.0", "hold_trade": "0.0"},
            "ZUSD": {"balance": "1_000_000.0", "hold_trade": "0.0"},
        }
        self.__fee = 0.0025

    def create_order(self: Self, **kwargs) -> dict:  # noqa: ANN003
        """Create a new order and update balances if needed."""
        txid = str(uuid.uuid4()).upper()
        order = {
            "userref": kwargs["userref"],
            "descr": {
                "pair": "XBTUSD",
                "type": kwargs["side"],
                "ordertype": kwargs["ordertype"],
                "price": kwargs["price"],
            },
            "status": "open",
            "vol": kwargs["volume"],
            "vol_exec": "0.0",
            "cost": "0.0",
            "fee": "0.0",
        }

        if kwargs["side"] == "buy":
            required_balance = float(kwargs["price"]) * float(kwargs["volume"])
            if float(self.__balances["ZUSD"]["balance"]) < required_balance:
                raise ValueError("Insufficient balance to create buy order")
            self.__balances["ZUSD"]["balance"] = str(
                float(self.__balances["ZUSD"]["balance"]) - required_balance,
            )
            self.__balances["ZUSD"]["hold_trade"] = str(
                float(self.__balances["ZUSD"]["hold_trade"]) + required_balance,
            )
        elif kwargs["side"] == "sell":
            if float(self.__balances["XXBT"]["balance"]) < float(kwargs["volume"]):
                raise ValueError("Insufficient balance to create sell order")
            self.__balances["XXBT"]["balance"] = str(
                float(self.__balances["XXBT"]["balance"]) - float(kwargs["volume"]),
            )
            self.__balances["XXBT"]["hold_trade"] = str(
                float(self.__balances["XXBT"]["hold_trade"]) + float(kwargs["volume"]),
            )

        self.__orders[txid] = order
        return {"txid": [txid]}

    def fill_order(self: Self, txid: str, volume: float | None = None) -> None:
        """Fill an order and update balances."""
        order = self.__orders.get(txid, {})
        if not order:
            return

        if volume is None:
            volume = float(order["vol"])

        if volume > float(order["vol"]) - float(order["vol_exec"]):
            raise ValueError(
                "Cannot fill order with volume higher than remaining order volume",
            )

        executed_volume = float(order["vol_exec"]) + volume
        remaining_volume = float(order["vol"]) - executed_volume

        order["fee"] = str(float(order["vol_exec"]) * self.__fee)
        order["vol_exec"] = str(executed_volume)
        order["cost"] = str(
            executed_volume * float(order["descr"]["price"]) + float(order["fee"]),
        )

        if remaining_volume <= 0:
            order["status"] = "closed"
        else:
            order["status"] = "open"

        self.__orders[txid] = order

        if order["descr"]["type"] == "buy":
            self.__balances["XXBT"]["balance"] = str(
                float(self.__balances["XXBT"]["balance"]) + volume,
            )
            self.__balances["ZUSD"]["balance"] = str(
                float(self.__balances["ZUSD"]["balance"]) - float(order["cost"]),
            )
            self.__balances["ZUSD"]["hold_trade"] = str(
                float(self.__balances["ZUSD"]["hold_trade"]) - float(order["cost"]),
            )
        elif order["descr"]["type"] == "sell":
            self.__balances["XXBT"]["balance"] = str(
                float(self.__balances["XXBT"]["balance"]) - volume,
            )
            self.__balances["XXBT"]["hold_trade"] = str(
                float(self.__balances["XXBT"]["hold_trade"]) - volume,
            )
            self.__balances["ZUSD"]["balance"] = str(
                float(self.__balances["ZUSD"]["balance"]) + float(order["cost"]),
            )

    async def on_ticker_update(self: Self, callback: Callable, last: float) -> None:
        """Update the ticker and fill orders if needed."""
        await callback(
            {
                "channel": "ticker",
                "data": [{"symbol": "BTC/USD", "last": last}],
            },
        )

        async def fill_order(txid: str) -> None:
            self.fill_order(txid)
            await callback(
                {
                    "channel": "executions",
                    "type": "update",
                    "data": [{"exec_type": "filled", "order_id": txid}],
                },
            )

        for txid, order in self.get_open_orders()["open"].items():
            if (
                order["descr"]["type"] == "buy"
                and float(order["descr"]["price"]) >= last
            ) or (
                order["descr"]["type"] == "sell"
                and float(order["descr"]["price"]) <= last
            ):
                await fill_order(txid=txid)

    def cancel_order(self: Self, txid: str) -> None:
        """Cancel an order and update balances if needed."""
        order = self.__orders.get(txid, {})
        if not order:
            return

        order.update({"status": "canceled"})
        self.__orders[txid] = order

        if order["descr"]["type"] == "buy":
            executed_cost = float(order["vol_exec"]) * float(order["descr"]["price"])
            remaining_cost = (
                float(order["vol"]) * float(order["descr"]["price"]) - executed_cost
            )
            self.__balances["ZUSD"]["balance"] = str(
                float(self.__balances["ZUSD"]["balance"]) + remaining_cost,
            )
            self.__balances["ZUSD"]["hold_trade"] = str(
                float(self.__balances["ZUSD"]["hold_trade"]) - remaining_cost,
            )
            self.__balances["XXBT"]["balance"] = str(
                float(self.__balances["XXBT"]["balance"]) - float(order["vol_exec"]),
            )
        elif order["descr"]["type"] == "sell":
            remaining_volume = float(order["vol"]) - float(order["vol_exec"])
            self.__balances["XXBT"]["balance"] = str(
                float(self.__balances["XXBT"]["balance"]) + remaining_volume,
            )
            self.__balances["XXBT"]["hold_trade"] = str(
                float(self.__balances["XXBT"]["hold_trade"]) - remaining_volume,
            )
            self.__balances["ZUSD"]["balance"] = str(
                float(self.__balances["ZUSD"]["balance"]) - float(order["cost"]),
            )

    def cancel_all_orders(self: Self, **kwargs: Any) -> None:  # noqa: ARG002
        """Cancel all open orders."""
        for txid in self.__orders:
            self.cancel_order(txid)

    def get_open_orders(self, **kwargs: Any) -> dict:  # noqa: ARG002
        """Get all open orders."""
        return {
            "open": {k: v for k, v in self.__orders.items() if v["status"] == "open"},
        }

    def get_orders_info(self: Self, txid: str) -> dict:
        """Get information about a specific order."""
        if order := self.__orders.get(txid, None):
            return {txid: order}
        return {}

    def get_balances(self: Self, **kwargs: Any) -> dict:  # noqa: ARG002
        """Get the user's current balances."""
        return deepcopy(self.__balances)


async def get_kraken_instance(
    bot_config: BotConfigDTO,
    db_config: DBConfigDTO,
    notification_config: NotificationConfigDTO,
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

    api = KrakenAPI()
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

    return engine
