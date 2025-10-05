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
from typing import Self

from infinity_grid.core.state_machine import States
from infinity_grid.models.configuration import (
    BotConfigDTO,
    DBConfigDTO,
    NotificationConfigDTO,
)

from ..framework.base_test_manager import BaseIntegrationTestManager

LOG = logging.getLogger(__name__)

from .kraken_api_mock import ExchangeTestConfig, KrakenMockAPI


class KrakenIntegrationTestManager(BaseIntegrationTestManager):
    """
    Kraken-specific integration test manager.

    This class demonstrates how to implement the exchange-agnostic
    framework for Kraken exchange.
    """

    def __init__(
        self: Self,
        bot_config: BotConfigDTO,
        db_config: DBConfigDTO,
        notification_config: NotificationConfigDTO,
        exchange_config: ExchangeTestConfig,
    ) -> None:
        super().__init__(
            bot_config=bot_config,
            db_config=db_config,
            notification_config=notification_config,
            exchange_config=exchange_config,
            mock_api_type=KrakenMockAPI,
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
