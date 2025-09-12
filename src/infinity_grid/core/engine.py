# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2023 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

import asyncio
import signal
import sys
from importlib.metadata import version
from logging import getLogger
from typing import Self

from infinity_grid.core.event_bus import EventBus
from infinity_grid.core.state_machine import StateMachine, States
from infinity_grid.exceptions import BotStateError, MetricsServerError
from infinity_grid.models.configuration import (
    BotConfigDTO,
    DBConfigDTO,
    MetricsConfigDTO,
    NotificationConfigDTO,
)
from infinity_grid.services.database import DBConnect
from infinity_grid.services.metrics_service import MetricsServer
from infinity_grid.services.notification_service import NotificationService
from infinity_grid.strategies.grid_base import GridStrategyBase

LOG = getLogger(__name__)


class BotEngine:
    """
    Orchestrates the trading bot's components and delegates specific
    responsibilities to specialized classes.
    """

    def __init__(
        self: Self,
        bot_config: BotConfigDTO,
        db_config: DBConfigDTO,
        notification_config: NotificationConfigDTO,
        metrics_config: MetricsConfigDTO | None = None,
    ) -> None:
        LOG.info(
            "Initiate the Infinity Grid algorithm instance (v%s)",
            version("infinity-grid"),
        )
        self.__event_bus = EventBus()
        self.__state_machine = StateMachine()
        self.__config = bot_config

        # == Infrastructure components =========================================
        ##
        self.__db = DBConnect(db_config)

        # == Application services ==============================================
        ##
        self.__notification_service = NotificationService(notification_config)

        # Metrics server (optional)
        self.__metrics_server = None
        if metrics_config and metrics_config.enabled:
            self.__metrics_server = MetricsServer(
                state_machine=self.__state_machine,
                config=metrics_config,
                verbosity=self.__config.verbosity,
            )

        # Create the appropriate strategy based on config
        self.__strategy = self.__strategy_factory()

        # Setup event subscriptions
        self.__setup_event_handlers()

    def __strategy_factory(self: Self) -> GridStrategyBase:
        from infinity_grid.strategies import (  # pylint: disable=import-outside-toplevel # noqa: PLC0415
            CDCAStrategy,
            GridHODLStrategy,
            GridSellStrategy,
            SwingStrategy,
        )

        if self.__config.strategy not in (
            strategies := {
                "SWING": SwingStrategy,
                "GridHODL": GridHODLStrategy,
                "GridSell": GridSellStrategy,
                "cDCA": CDCAStrategy,
            }
        ):
            raise ValueError(f"Unknown strategy type: {self.__config.strategy}")

        return strategies[self.__config.strategy](
            config=self.__config,
            state_machine=self.__state_machine,
            event_bus=self.__event_bus,
            db=self.__db,
        )

    def __setup_event_handlers(self: Self) -> None:
        # Subscribe to events
        self.__event_bus.subscribe("on_message", self.__strategy.on_message)
        self.__event_bus.subscribe(
            "notification",
            self.__notification_service.on_notification,
        )

    async def run(self: Self) -> None:
        """Start the bot"""
        LOG.info("Starting the Infinity Grid Algorithm...")

        # ======================================================================
        # Start metrics server if enabled
        ##
        if self.__metrics_server:
            try:
                await self.__metrics_server.start()
            except MetricsServerError as e:
                LOG.warning("Failed to start metrics server: %s", e)
                # Continue without metrics server
                self.__metrics_server = None

        # ======================================================================
        # Handle the shutdown signals
        #
        # A controlled shutdown is initiated by sending a SIGINT or SIGTERM
        # signal to the process. Since requests and database interactions are
        # executed synchronously, we only need to set the stop_event during
        # on_message, ensuring no further messages are processed.
        ##
        def _signal_handler() -> None:
            LOG.warning("Initiate a controlled shutdown of the algorithm...")
            self.__state_machine.transition_to(States.SHUTDOWN_REQUESTED)

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _signal_handler)

        # ======================================================================
        # Start running the strategy
        ##
        try:
            # Wait for shutdown
            await asyncio.wait(
                [
                    asyncio.create_task(self.__state_machine.wait_for_shutdown()),
                    asyncio.create_task(self.__strategy.run()),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )
        except asyncio.CancelledError as exc:
            self.__state_machine.transition_to(States.ERROR)
            await asyncio.sleep(5)
            await self.terminate(f"The algorithm was interrupted: {exc}")
        except (
            BotStateError,
            Exception,
        ) as exc:  # pylint: disable=broad-exception-caught
            self.__state_machine.transition_to(States.ERROR)
            await asyncio.sleep(5)
            await self.terminate(f"The algorithm was interrupted by exception: {exc}")

        await asyncio.sleep(5)

        if self.__state_machine.state == States.SHUTDOWN_REQUESTED:
            # The algorithm was interrupted by a signal.
            await self.terminate(
                "The algorithm was shut down successfully!",
                exception=False,
            )
        elif self.__state_machine.state == States.ERROR:
            await self.terminate(
                "The algorithm was shut down due to an error!",
            )

    async def terminate(
        self: Self,
        reason: str = "",
        *,
        exception: bool = True,
    ) -> None:
        """
        Handle the termination of the algorithm.

        1. Stops the metrics server if running
        2. Stops the websocket connections and aiohttp sessions managed by the
           python-kraken-sdk
        3. Stops the connection to the database.
        4. Notifies the user via Telegram about the termination.
        5. Exits the algorithm.
        """
        # Stop metrics server
        if self.__metrics_server:
            try:
                await self.__metrics_server.stop()
            except MetricsServerError as e:
                LOG.warning("Failed to stop metrics server: %s", e)

        await self.__strategy.stop()
        self.__db.close()

        self.__event_bus.publish(
            "notification",
            data={"message": f"{self.__config.name} terminated.\nReason: {reason}"},
        )
        sys.exit(exception)
