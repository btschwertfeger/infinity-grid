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
        """
        Check if the API key permissions are set correctly. This function
        ideally runs various requests to API endpoints to ensure that they are
        available by the passed API credentials.
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def check_exchange_status(self: Self, tries: int = 0) -> None:
        """
        Check if the exchange is online and operational.

        :param tries: Tries to take to check if the exchange is available,
            defaults to ``0``
        :type tries: int
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    # == Getters for exchange user operations ==================================
    @abstractmethod
    def get_orders_info(self: Self, txid: str | None) -> OrderInfoSchema | None:
        """
        Retrieves order information from the exchange based on passed
        transaction ID.

        :param txid: The transaction or order ID to filter for , defaults to ``None``
        :type: str | None
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_open_orders(
        self: Self,
        userref: int,
        trades: bool | None = None,
    ) -> list[OrderInfoSchema]:
        """
        Retrieve all open orders based on a user reference number.

        :param userref: The reference number to filter orders for
        :type userref: int
        :param trades: Include trades in the result, defaults to ``None``
        :type trades: bool | None, optional
        :rtype: list[OrderInfoSchema]
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_order_with_retry(
        self: Self,
        txid: str,
        tries: int = 0,
        max_tries: int = 5,
        exit_on_fail: bool = True,
    ) -> OrderInfoSchema:
        """
        Get order information with retry logic.

        If ``exit_on_fail`` is ``True``, the algorithm must transition to the
        error state of the state machine and terminate accordingly. For more
        information please conduct the documentation of the state machine of the
        infinity-grid.

        :param txid: The transaction or order ID
        :type txid: str
        :param tries: The current try to retrieve the order information,
            defaults to ``0``
        :type tries: ``int``, optional
        :param max_tries: The maximum number of tries, defaults to ``5``
        :type max_tries: int, optional
        :param exit_on_fail: Exit the algorithm via error state if the order
            could not be retrieved, defaults to ``True``
        :type exit_on_fail: bool, optional
        :rtype: OrderInfoSchema
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_account_balance(self: Self) -> dict[str, float]:
        """
        Get the account balances.

        Note: This function is currently only needed by the Kraken adapter in
              order to check the permissions.
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_closed_orders(self: Self, userref: int, trades: bool) -> dict[str, Any]:
        """
        Get closed orders for a userref with an optional limit.

        Note: This function is currently only needed by the Kraken adapter in
              order to check the permissions.
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_balances(self: Self) -> list[AssetBalanceSchema]:
        """
        Get the current balances of the account.
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_pair_balance(self: Self) -> PairBalanceSchema:
        """Get the balance for a specific currency pair."""
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @property
    @abstractmethod
    def rest_symbol(self: Self) -> str:
        """
        Returns the symbol for the given base and quote currency.

        This method must be implemented with the ``@cached_property`` or
        ``@property`` decorator.

        Examples for the Kraken Crypto Asset Exchange adapter
        - BTC/USD for Bitcoin and US Dollar
        - DOT/USD for Polkadot and US Dollar
        - AVAX/EUR for Avalanche and Euro
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @property
    @abstractmethod
    def rest_altname(self: Self) -> str:
        """
        Returns the alternative name for the given base and quote currency.

        The return value must match the value of the ``pair`` property of the
        :py:class:`infinity_grid.models.exchange.OrderInfoSchema`. This value is
        often used to compar the pair with pairs of orders and messages being
        processed.

        This method must be implemented with the ``@cached_property`` or
        ``@property`` decorator.

        Examples for the Kraken Crypto Asset Exchange adapter
        - BTCUSD for Bitcoin and US Dollar
        - DOTUSD for Polkadot and US Dollar
        - AVAXEUR for Avalanche and Euro
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @property
    @abstractmethod
    def ws_symbol(self: Self) -> str:
        """
        Returns the websocket symbol for the given base and quote currency.

        The return value is used to subscribe and un-subscribe from websocket
        channels.

        This method must be implemented with the @cached_property or @property
        decorator.
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @property
    @abstractmethod
    def ws_altname(self) -> str:
        """Returns the alternative name for the given base and quote currency.

        The return value is currently not used.

        This method must be implemented with the @cached_property or @property
        decorator.
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
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
        """
        Create a new order.

        :param ordertype: The kind of the order, e.g. ``limit``
        :type ordertype: str
        :param side: The side of the order, e.g. ``buy`` or ``sell``
        :type side: str
        :param volume: The volume of the order
        :type volume: float
        :param price: The price to place the order
        :type price: float
        :param userref: The user reference number to refer
        :type userref: int
        :param validate: If the order should just be validated, but not placed,
            similar to a dry run, defaults to ``False``
        :type validate: ``bool``, optional
        :param oflags: Additional order flags to use, defaults to ``None``
        :type oflags: ``str | None``, optional
        :rtype: CreateOrderResponseSchema
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def cancel_order(self: Self, txid: str) -> None:
        """
        Cancel an order based on transaction/order ID.

        :param txid: The order ID of the order to cancel.
        :type txid: str
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def truncate(self: Self, amount: float | Decimal | str, amount_type: str) -> str:
        """
        Truncate amount according to exchange precision. This allows to exactly
        match the precision that some exchanges might require.

        .. code-block:: python
            :linenos:
            :caption: Truncate XBTUSD

            >>> print(truncate(amount=0.123456789, amount_type="volume"))
            0.12345678

            >>> print(truncate(amount=21123.12849829993, amount_type="price")))
            21123.1

        :param amount: The value that needs to be truncated
        :type amount: float | Decimal | str
        :param amount_type: What the amount represents. Either ``"price"`` or
            ``"volume"``.
        :type amount_type: str
        :rtype: str
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    # == Getters for exchange market operations ================================
    @abstractmethod
    def get_system_status(self: Self) -> str:
        """
        Get the current system status of the exchange.

        Must return ``"online"`` to succeed.
        """
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_asset_pair_info(self: Self) -> AssetPairInfoSchema:
        """Get available asset pair info from the exchange."""
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @abstractmethod
    def get_exchange_domain(self: Self) -> ExchangeDomain:
        """Return the exchange-specific naming conventions."""
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
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
            "This method must be implemented in the concrete exchange class.",
        )

    @abstractmethod
    async def start(self: Self) -> None:
        """Start the websocket connection."""
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @abstractmethod
    async def close(self: Self) -> None:
        """Close the websocket connection."""
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @abstractmethod
    async def subscribe(self: Self, params: dict[str, Any]) -> None:
        """Subscribe to a specific channel and pair."""
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )

    @abstractmethod
    async def on_message(self: Self, message: OnMessageSchema) -> None:
        """Function called on every received message."""
        raise NotImplementedError(
            "This method must be implemented in the concrete exchange class.",
        )
