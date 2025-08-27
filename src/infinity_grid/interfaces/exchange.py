# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Interfaces for the Infinity Grid Bot

FIXME: Add comprehensive examples and documentation for each method.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Self

from infinity_grid.core.event_bus import EventBus
from infinity_grid.core.state_machine import StateMachine
from infinity_grid.models.exchange import (
    AssetBalanceSchema,
    AssetPairInfoSchema,
    CreateOrderResponseSchema,
    ExchangeDomain,
    OnMessageSchema,
    OrderInfoSchema,
    PairBalanceSchema,
)


class IExchangeRESTService(ABC):
    """Interface for exchange operations."""

    @abstractmethod
    def __init__(
        self: Self,
        api_public_key: str,
        api_secret_key: str,
        state_machine: StateMachine,
        base_currency: str,
        quote_currency: str,
    ) -> None:
        """Initialize the REST service"""

    @abstractmethod
    def check_api_key_permissions(self: Self) -> None:
        """Check if the API key permissions are set correctly."""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def check_exchange_status(self: Self, tries: int = 0) -> None:
        """Check if the exchange is online and operational.

        Raises an exception if the exchange is not online.
        """
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    # == Getters for exchange user operations ==================================
    @abstractmethod
    def get_orders_info(self: Self, txid: str | None) -> OrderInfoSchema | None:
        """Get information about the user on the exchange."""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_open_orders(
        self: Self,
        userref: int,
        trades: bool | None = None,
    ) -> list[OrderInfoSchema]:
        """Get all open orders for a userref."""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_order_with_retry(
        self: Self,
        txid: str,
        tries: int = 0,
        max_tries: int = 5,
        exit_on_fail: bool = True,
    ) -> OrderInfoSchema:
        """Get order information with retry logic.

        If exit_on_fail is True, the program will exit if the order cannot be retrieved.
        """
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_account_balance(self: Self) -> dict[str, float]:
        """Get the current account balance."""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_closed_orders(
        self: Self,
        userref: int,
        trades: bool,
    ) -> dict[str, Any]:
        """Get closed orders for a userref with an optional limit."""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_balances(self: Self) -> list[AssetBalanceSchema]:
        """Get current balances."""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_pair_balance(
        self: Self,
    ) -> PairBalanceSchema:
        """Get the balance for a specific currency pair."""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @property
    @abstractmethod
    def rest_symbol(self: Self) -> str:
        """
        Returns the symbol for the given base and quote currency.

        This method must be implemented with the @cached_property or @property
        decorator.
        """
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @property
    @abstractmethod
    def rest_altname(self: Self) -> str:
        """
        Returns the alternative name for the given base and quote currency.

        This method must be implemented with the @cached_property or @property
        decorator.
        """
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @property
    @abstractmethod
    def ws_symbol(self: Self) -> str:
        """Returns the symbol for the given base and quote currency.

        This method must be implemented with the @cached_property or @property
        decorator.
        """
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @property
    @abstractmethod
    def ws_altname(self) -> str:
        """Returns the alternative name for the given base and quote currency

        This method must be implemented with the @cached_property or @property
        decorator.
        """
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    # == Getters for exchange trade operations =================================
    @abstractmethod
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
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def cancel_order(self: Self, txid: str) -> None:
        """Cancel an order."""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def truncate(self: Self, amount: float | Decimal | str, amount_type: str) -> str:
        """Truncate amount according to exchange precision."""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    # == Getters for exchange market operations ================================
    @abstractmethod
    def get_system_status(self: Self) -> str:
        """
        Get the current system status of the exchange.

        Must be "online" to succeed.
        """
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_asset_pair_info(
        self: Self,
    ) -> AssetPairInfoSchema:
        """Get available asset pair info from the exchange."""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_exchange_domain(self: Self) -> ExchangeDomain:
        """Get the current order side (buy/sell) for the strategy."""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )


class IExchangeWebSocketService(ABC):
    """Interface for exchange websocket operations."""

    @abstractmethod
    def __init__(
        self: Self,
        api_public_key: str,
        api_secret_key: str,
        event_bus: EventBus,
        state_machine: StateMachine,
    ) -> None:
        """Initialize the Websocket service"""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @abstractmethod
    async def start(self: Self) -> None:
        """Start the websocket connection."""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @abstractmethod
    async def close(self: Self) -> None:
        """Close the websocket connection."""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @abstractmethod
    async def subscribe(self: Self, params: dict[str, Any]) -> None:
        """Subscribe to a specific channel and pair."""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )

    @abstractmethod
    async def on_message(self: Self, message: OnMessageSchema) -> None:
        """Function called on every received message."""
        raise NotImplementedError(
            "This method should be implemented in the concrete exchange class.",
        )
