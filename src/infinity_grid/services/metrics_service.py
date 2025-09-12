# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Metrics and health check HTTP server for the Infinity Grid trading bot."""

import json
import time
from datetime import datetime, timezone
from logging import getLogger
from typing import Self

from aiohttp import web
from aiohttp.web import Application, Request, Response

from infinity_grid.core.state_machine import StateMachine
from infinity_grid.exceptions import MetricsServerError
from infinity_grid.models.configuration import MetricsConfigDTO

LOG = getLogger(__name__)


class MetricsServer:
    """HTTP server that provides metrics endpoints."""

    def __init__(
        self: Self,
        state_machine: StateMachine,
        config: MetricsConfigDTO,
        verbosity: int,
    ) -> None:
        self._state_machine: StateMachine = state_machine
        self._port: int = config.port
        self._host: str = config.host
        self._verbosity: int = verbosity
        self._app: Application | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._start_time: float = time.time()

    def _setup_routes(self: Self) -> Application:
        """Setup HTTP routes for the metrics server."""
        app = web.Application()
        app.router.add_get("/status", self._status_handler)
        app.router.add_get("/", self._root_handler)
        return app

    async def _status_handler(self: Self, request: Request) -> Response:  # noqa: ARG002
        """Status endpoint that returns current bot status."""
        return Response(
            text=json.dumps(
                {
                    "state": self._state_machine.state.name,
                    "uptime_seconds": time.time() - self._start_time,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
            ),
            status=200,
            content_type="application/json",
        )

    async def _root_handler(self: Self, request: Request) -> Response:  # noqa: ARG002
        """Root endpoint that returns available endpoints."""
        return Response(
            text=json.dumps(
                {
                    "endpoints": {
                        "/": "This help message",
                        "/status": "Current bot status",
                    },
                    "bot_state": self._state_machine.state.name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
            ),
            status=200,
            content_type="application/json",
        )

    async def start(self: Self) -> None:
        """Start the metrics server."""
        try:
            LOG.debug("Starting metrics server on %s:%s", self._host, self._port)

            self._app = self._setup_routes()
            self._runner = web.AppRunner(
                self._app,
                access_log=LOG if self._verbosity != 0 else None,
            )
            await self._runner.setup()

            self._site = web.TCPSite(self._runner, self._host, self._port)
            await self._site.start()

            LOG.info(
                "Metrics server started successfully on http://%s:%s",
                self._host,
                self._port,
            )
        except Exception as exc:
            LOG.error("Failed to start metrics server: %s", exc)
            raise MetricsServerError(
                f"Failed to start metrics server on {self._host}:{self._port}",
            ) from exc

    async def stop(self: Self) -> None:
        """Stop the metrics server."""
        try:
            LOG.info("Stopping metrics server...")

            if self._site:
                await self._site.stop()
                self._site = None

            if self._runner:
                await self._runner.cleanup()
                self._runner = None

            self._app = None
            LOG.info("Metrics server stopped successfully")
        except Exception as exc:
            LOG.error("Failed to stop metrics server: %s", exc)
            raise MetricsServerError("Failed to stop metrics server") from exc
