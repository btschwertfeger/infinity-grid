# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

import pytest

from .kraken_exchange_api import KrakenExchangeAPIConfig


@pytest.fixture(scope="session")
def kraken_config_xbtusd() -> KrakenExchangeAPIConfig:
    return KrakenExchangeAPIConfig(
        base_currency="XXBT",
        quote_currency="ZUSD",
        pair="XBTUSD",
        ws_symbol="BTC/USD",
    )


@pytest.fixture(scope="session")
def kraken_config_aaplxusd() -> KrakenExchangeAPIConfig:
    return KrakenExchangeAPIConfig(
        base_currency="AAPLx",
        quote_currency="ZUSD",
        pair="AAPLxUSD",
        ws_symbol="AAPLx/USD",
    )
