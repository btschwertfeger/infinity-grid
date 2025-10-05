# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

import pytest

from infinity_grid.models.configuration import NotificationConfigDTO, TelegramConfigDTO


from typing import Callable

import pytest

from infinity_grid.models.configuration import (
    BotConfigDTO,
    DBConfigDTO,
    NotificationConfigDTO,
)

from .framework.base_test_manager import ExchangeTestConfig, BaseIntegrationTestManager



@pytest.fixture(scope="session")
def notification_config() -> NotificationConfigDTO:
    return NotificationConfigDTO(telegram=TelegramConfigDTO(token=None, chat_id=None))

@pytest.fixture
def exchange_config_factory() -> Callable:
    """
    Factory to create ExchangeTestConfig instances for different symbols.
    """

    def _factory(symbol: str) -> ExchangeTestConfig:
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
        raise ValueError(f"Unknown symbol {symbol!r}")

    return _factory


@pytest.fixture
def bot_config_factory() -> Callable:
    """Factory to create BotConfigDTO instances for different symbols."""

    def _make_bot_config(
        exchange: str, strategy: str, base_currency: str, quote_currency: str,
    ) -> BotConfigDTO:
        return BotConfigDTO(
            strategy=strategy,
            exchange=exchange,
            api_public_key="",
            api_secret_key="",
            name=f"Local Tests Bot GridHODL {base_currency}{quote_currency}",
            userref=0,
            base_currency=base_currency,
            quote_currency=quote_currency,
            max_investment=10_000.0,
            amount_per_grid=100.0,
            interval=0.01,
            n_open_buy_orders=5,
            verbosity=0,
        )

    def _factory(exchange: str, symbol: str, strategy: str) -> BotConfigDTO:
        if exchange == "Kraken":
            if symbol == "XBTUSD":
                return _make_bot_config(exchange, strategy, "BTC", "USD")
            if symbol == "AAPLxUSD":
                return _make_bot_config(exchange, strategy, "AAPLx", "USD")
            raise ValueError(f"Unknown bot config symbol for {exchange}: {symbol}")
        raise ValueError(f"Unknown exchange for bot config: {exchange}")
    return _factory

@pytest.fixture
def test_manager_factory(
    db_config: DBConfigDTO,
    notification_config: NotificationConfigDTO,
    bot_config_factory: Callable[[str, str], BotConfigDTO],
    exchange_config_factory: Callable[[str], ExchangeTestConfig],
) -> BaseIntegrationTestManager:

    def _factory(
        exchange: str,
        symbol: str,
        strategy: str,
    ) -> BaseIntegrationTestManager:

        manager = None
        if exchange == "Kraken":
            from .kraken_exchange.kraken_test_manager import KrakenIntegrationTestManager

            manager = KrakenIntegrationTestManager
        else:
            raise ValueError(f"Unknown exchange: {exchange}")

        return manager(
            bot_config=bot_config_factory(exchange, symbol, strategy),
            notification_config=notification_config,
            db_config=db_config,
            exchange_config=exchange_config_factory( symbol),
        )

    return _factory

