# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#
# pylint: disable=arguments-differ

"""This module contains a mocked Kraken API used during integration tests."""

import logging
import uuid
from copy import deepcopy
from decimal import Decimal
from functools import lru_cache
from typing import Any, Callable, Self

from kraken.spot import Market, Trade, User
from pydantic import BaseModel

LOG = logging.getLogger(__name__)


class KrakenExchangeAPIConfig(BaseModel):
    base_currency: str  # e.g., "XBT"
    quote_currency: str  # e.g., "ZUSD"
    pair: str  # e.g., "XBTUSD"
    ws_symbol: str  # e.g., "BTC/USD"


class Balances(dict):  # noqa: FURB189
    def __init__(
        self: Self,
        *args: Any,
        base_currency: str,
        quote_currency: str,
        truncate_cost: Callable[[float | Decimal], str],
        truncate_base: Callable[[float | Decimal], str],
        **kwargs: Any,
    ) -> None:
        self.truncate_cost = truncate_cost
        self.truncate_base = truncate_base
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        super().__init__(*args, **kwargs)

    def __setitem__(self: Self, key: str, value: dict) -> None:
        # key is currency, value is dict with 'balance' and 'hold_trade'
        if key == self.base_currency:
            value = {
                "balance": f"{self.truncate_base(value['balance'])}",
                "hold_trade": f"{self.truncate_base(value['hold_trade'])}",
            }
        elif key == self.quote_currency:
            value = {
                "balance": f"{self.truncate_cost(value['balance'])}",
                "hold_trade": f"{self.truncate_cost(value['hold_trade'])}",
            }
        super().__setitem__(key, value)

    def __getitem__(self: Self, key: str) -> dict:
        return super().__getitem__(key)


class KrakenAPI(Market, Trade, User):
    """
    Class extending the Market, Trade, and User client of the python-kraken-sdk
    to use its methods for non-authenticated requests.

    This class tries to simulate the backend of the Kraken Exchange, handling
    orders and trades used during tests.
    """

    def __init__(
        self: Self,
        exchange_config: KrakenExchangeAPIConfig,
    ) -> None:
        super().__init__()  # DONT PASS SECRETS!
        self.__orders = {}

        # FIXME: make customizable via kraken_config
        self.cost_decimal_places = 5
        self.base_decimal_places = 8

        # Use for balance retrieval and updates. Kraken suffixes tokenized
        # assets with '.T'
        if exchange_config.base_currency.endswith("x"):
            exchange_config.base_currency += ".T"

        self.__balances = Balances(
            {
                exchange_config.base_currency: {
                    "balance": self.truncate_base("100.0"),
                    "hold_trade": self.truncate_base("0.0"),
                },
                exchange_config.quote_currency: {
                    "balance": self.truncate_cost("1000000.00000000"),
                    "hold_trade": self.truncate_cost("0.00000000"),
                },
            },
            truncate_cost=self.truncate_cost,
            truncate_base=self.truncate_base,
            base_currency=exchange_config.base_currency,
            quote_currency=exchange_config.quote_currency,
        )
        self.__fee = 0.0025
        self.__base_currency = exchange_config.base_currency
        self.__quote_currency = exchange_config.quote_currency
        self.__pair = exchange_config.pair
        self.__ws_symbol = exchange_config.ws_symbol

    def create_order(self: Self, **kwargs) -> dict:  # noqa: ANN003
        """Create a new order and update balances if needed."""
        txid = str(uuid.uuid4()).upper()
        order = {
            "userref": kwargs["userref"],
            "descr": {
                "pair": self.__pair,
                "type": kwargs["side"],
                "ordertype": kwargs["ordertype"],
                "price": self.truncate_cost(kwargs["price"]),
            },
            "status": "open",
            "vol": Decimal(kwargs["volume"]),
            "vol_exec": self.truncate_base("0.0"),
            "cost": self.truncate_cost("0.0"),
            "fee": self.truncate_cost("0.0"),
        }

        if kwargs["side"] == "buy":
            required_balance = Decimal(kwargs["price"]) * Decimal(kwargs["volume"])
            if (
                Decimal(self.__balances[self.__quote_currency]["balance"])
                < required_balance
            ):
                raise ValueError("Insufficient balance to create buy order")
            self.__balances[self.__quote_currency]["balance"] = str(
                Decimal(self.__balances[self.__quote_currency]["balance"])
                - required_balance,
            )
            self.__balances[self.__quote_currency]["hold_trade"] = str(
                Decimal(self.__balances[self.__quote_currency]["hold_trade"])
                + required_balance,
            )
        elif kwargs["side"] == "sell":
            if Decimal(self.__balances[self.__base_currency]["balance"]) < Decimal(
                kwargs["volume"],
            ):
                raise ValueError("Insufficient balance to create sell order")
            self.__balances[self.__base_currency]["balance"] = str(
                Decimal(self.__balances[self.__base_currency]["balance"])
                - Decimal(kwargs["volume"]),
            )
            self.__balances[self.__base_currency]["hold_trade"] = str(
                Decimal(self.__balances[self.__base_currency]["hold_trade"])
                + Decimal(kwargs["volume"]),
            )

        self.__orders[txid] = order
        return {"txid": [txid]}

    def fill_order(self: Self, txid: str, volume: float | None = None) -> None:
        """Fill an order and update balances."""
        order = self.__orders.get(txid, {})
        if not order:
            return

        if volume is None:
            volume = Decimal(self.truncate_base(Decimal(order["vol"])))
        else:
            volume = Decimal(self.truncate_base(Decimal(volume)))
        LOG.debug("Filling order %s with volume %s", txid, volume)

        if volume > (
            remaining_volume := Decimal(order["vol"]) - Decimal(order["vol_exec"])
        ) and abs(remaining_volume) < Decimal(1).scaleb(-self.base_decimal_places):
            raise ValueError(
                "Cannot fill order with volume higher than remaining order volume.",
                remaining_volume,
            )

        executed_volume = Decimal(order["vol_exec"]) + Decimal(volume)
        remaining_volume = Decimal(order["vol"]) - executed_volume

        if abs(remaining_volume) < Decimal(1).scaleb(-self.base_decimal_places):
            remaining_volume = Decimal("0.0")
            executed_volume = Decimal(order["vol"])

        order["fee"] = str(Decimal(order["vol_exec"]) * Decimal(self.__fee))
        order["vol_exec"] = str(executed_volume)
        order["cost"] = str(
            executed_volume * Decimal(order["descr"]["price"]) + Decimal(order["fee"]),
        )

        if remaining_volume <= 0:
            order["status"] = "closed"
        else:
            order["status"] = "open"

        self.__orders[txid] = order

        if order["descr"]["type"] == "buy":
            self.__balances[self.__base_currency]["balance"] = str(
                Decimal(self.__balances[self.__base_currency]["balance"]) + volume,
            )
            self.__balances[self.__quote_currency]["balance"] = str(
                Decimal(self.__balances[self.__quote_currency]["balance"])
                - Decimal(order["cost"]),
            )
            self.__balances[self.__quote_currency]["hold_trade"] = str(
                Decimal(self.__balances[self.__quote_currency]["hold_trade"])
                - Decimal(order["cost"]),
            )
        elif order["descr"]["type"] == "sell":
            self.__balances[self.__base_currency]["balance"] = str(
                Decimal(self.__balances[self.__base_currency]["balance"]) - volume,
            )
            self.__balances[self.__base_currency]["hold_trade"] = str(
                Decimal(self.__balances[self.__base_currency]["hold_trade"]) - volume,
            )
            self.__balances[self.__quote_currency]["balance"] = str(
                Decimal(self.__balances[self.__quote_currency]["balance"])
                + Decimal(order["cost"]),
            )

    async def on_ticker_update(self: Self, callback: Callable, last: float) -> None:
        """Update the ticker and fill orders if needed."""
        await callback(
            {
                "channel": "ticker",
                "data": [{"symbol": self.__ws_symbol, "last": last}],
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
                and Decimal(order["descr"]["price"]) >= Decimal(last)
            ) or (
                order["descr"]["type"] == "sell"
                and Decimal(order["descr"]["price"]) <= Decimal(last)
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
            executed_cost = Decimal(order["vol_exec"]) * Decimal(
                order["descr"]["price"],
            )
            remaining_cost = (
                Decimal(order["vol"]) * Decimal(order["descr"]["price"]) - executed_cost
            )
            self.__balances[self.__quote_currency]["balance"] = str(
                Decimal(self.__balances[self.__quote_currency]["balance"])
                + remaining_cost,
            )
            self.__balances[self.__quote_currency]["hold_trade"] = str(
                Decimal(self.__balances[self.__quote_currency]["hold_trade"])
                - remaining_cost,
            )
            self.__balances[self.__base_currency]["balance"] = str(
                Decimal(self.__balances[self.__base_currency]["balance"])
                - Decimal(order["vol_exec"]),
            )
        elif order["descr"]["type"] == "sell":
            remaining_volume = Decimal(order["vol"]) - Decimal(order["vol_exec"])
            self.__balances[self.__base_currency]["balance"] = str(
                Decimal(self.__balances[self.__base_currency]["balance"])
                + remaining_volume,
            )
            self.__balances[self.__base_currency]["hold_trade"] = str(
                Decimal(self.__balances[self.__base_currency]["hold_trade"])
                - remaining_volume,
            )
            self.__balances[self.__quote_currency]["balance"] = str(
                Decimal(self.__balances[self.__quote_currency]["balance"])
                - Decimal(order["cost"]),
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

    @lru_cache(maxsize=1024)  # noqa: B019
    def truncate_cost(self: Self, value: float | Decimal) -> str:
        return f"{Decimal(value):.{self.cost_decimal_places}f}"

    @lru_cache(maxsize=1024)  # noqa: B019
    def truncate_base(self: Self, value: float | Decimal) -> str:
        return f"{Decimal(value):.{self.base_decimal_places}f}"
