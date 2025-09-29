# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

from typing import Callable

import pytest

from infinity_grid.models.configuration import (
    BotConfigDTO,
    DBConfigDTO,
    NotificationConfigDTO,
)

from .kraken_exchange_api import KrakenExchangeAPIConfig


@pytest.fixture
def kraken_exchange_config_factory() -> Callable:
    """
    Factory to create KrakenExchangeAPIConfig instances for different symbols.
    """

    def _factory(symbol: str) -> KrakenExchangeAPIConfig:
        if symbol == "XBTUSD":
            return KrakenExchangeAPIConfig(
                base_currency="XXBT",
                quote_currency="ZUSD",
                pair="XBTUSD",
                ws_symbol="BTC/USD",
            )
        if symbol == "AAPLxUSD":
            return KrakenExchangeAPIConfig(
                base_currency="AAPLx",
                quote_currency="ZUSD",
                pair="AAPLxUSD",
                ws_symbol="AAPLx/USD",
            )
        raise ValueError(f"Unknown kraken_exchange_config symbol {symbol!r}")

    return _factory


@pytest.fixture
def kraken_bot_config_factory() -> Callable:
    """Factory to create BotConfigDTO instances for different symbols."""

    def _make_kraken_gridhodl_bot_config(
        strategy: str,
        base_currency: str,
        quote_currency: str = "USD",
    ) -> BotConfigDTO:
        return BotConfigDTO(
            strategy=strategy,
            exchange="Kraken",
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

    def _factory(symbol: str, strategy: str) -> BotConfigDTO:
        if symbol == "XBTUSD":
            return _make_kraken_gridhodl_bot_config(strategy, "BTC", "USD")
        if symbol == "AAPLxUSD":
            return _make_kraken_gridhodl_bot_config(strategy, "AAPLx", "USD")
        raise ValueError(f"Unknown bot config symbol: {symbol}")

    return _factory


@pytest.fixture
def kraken_test_manager_factory(
    db_config: DBConfigDTO,
    notification_config: NotificationConfigDTO,
    kraken_bot_config_factory: Callable[[str, str], BotConfigDTO],
    kraken_exchange_config_factory: Callable[[str], KrakenExchangeAPIConfig],
) -> Callable:
    """
    Factory to create KrakenTestManager instances for different symbols and
    strategies.
    """
    from .helper import KrakenTestManager

    def _factory(symbol: str, strategy: str) -> KrakenTestManager:
        return KrakenTestManager(
            bot_config=kraken_bot_config_factory(symbol, strategy),
            notification_config=notification_config,
            db_config=db_config,
            kraken_config=kraken_exchange_config_factory(symbol),
        )

    return _factory
