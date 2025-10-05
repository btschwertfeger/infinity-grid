# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Kraken-specific implementation of the integration testing framework.

This module demonstrates how to implement the exchange-agnostic testing
framework for a specific exchange (Kraken), showing the pattern that
should be followed for other exchanges.
"""

import logging

from infinity_grid.models.configuration import (
    BotConfigDTO,
    DBConfigDTO,
    NotificationConfigDTO,
)

from ..framework.base_test_manager import BaseIntegrationTestManager
from typing import Self
from infinity_grid.core.state_machine import States
from infinity_grid.core.engine import BotEngine
LOG = logging.getLogger(__name__)

from .kraken_api_mock import KrakenMockAPI,ExchangeTestConfig


async def get_kraken_instance(
    bot_config: BotConfigDTO,
    db_config: DBConfigDTO,
    notification_config: NotificationConfigDTO,
    kraken_config: KrakenMockAPI,
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

    api = KrakenMockAPI(kraken_config)
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


class KrakenIntegrationTestManager(BaseIntegrationTestManager):
    """
    Kraken-specific integration test manager.

    This class demonstrates how to implement the exchange-agnostic
    framework for Kraken exchange.
    """

    async def initialize_engine(self) -> None:
        """Initialize the BotEngine with Kraken-specific adapters."""

        self._engine, self._mock_api = await get_kraken_instance(
            bot_config=self.bot_config,
            notification_config=self._notification_config,
            db_config=self._db_config,
            kraken_config=self.exchange_config,
        )

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

        await self._mock_api.simulate_ticker_update(
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



# Factory functions for easier test setup
def create_kraken_config(symbol: str) -> ExchangeTestConfig:
    """Factory to create KrakenExchangeConfig for different symbols."""
    if symbol == "XBTUSD":
        return ExchangeTestConfig(
            base_currency="XXBT",
            quote_currency="ZUSD",
            pair="XBTUSD",
            ws_symbol="BTC/USD",
        )
    if symbol == "AAPLxUSD":
        return ExchangeTestConfig(
            base_currency="AAPLx",
            quote_currency="ZUSD",
            pair="AAPLxUSD",
            ws_symbol="AAPLx/USD",
        )
    raise ValueError(f"Unknown symbol: {symbol}")


def create_kraken_bot_config(
    symbol: str,
    strategy: str,
) -> BotConfigDTO:
    """Factory to create BotConfigDTO for Kraken tests."""
    config_map = {
        "XBTUSD": {"base": "BTC", "quote": "USD"},
        "AAPLxUSD": {"base": "AAPLx", "quote": "USD"},
    }

    if symbol not in config_map:
        raise ValueError(f"Unknown symbol: {symbol}")

    currencies = config_map[symbol]

    return BotConfigDTO(
        strategy=strategy,
        exchange="Kraken",
        api_public_key="",
        api_secret_key="",
        name=f"Test Bot {strategy} {currencies['base']}{currencies['quote']}",
        userref=0,
        base_currency=currencies["base"],
        quote_currency=currencies["quote"],
        max_investment=10_000.0,
        amount_per_grid=100.0,
        interval=0.01,
        n_open_buy_orders=5,
        verbosity=0,
    )
