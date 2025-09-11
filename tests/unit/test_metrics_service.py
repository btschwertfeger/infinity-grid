# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Test module for metrics service.

This module contains focused tests for the MetricsServer class,
testing the HTTP server functionality, endpoints, and error handling.
"""

import json
import logging
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from aiohttp.test_utils import make_mocked_request
from aiohttp.web import Application

from infinity_grid.core.state_machine import StateMachine, States
from infinity_grid.exceptions import MetricsServerError
from infinity_grid.models.configuration import MetricsConfigDTO
from infinity_grid.services.metrics_service import MetricsServer


class TestMetricsServer:
    """Test cases for MetricsServer"""

    @pytest.fixture
    def state_machine(self) -> StateMachine:
        """Create a mock state machine for testing."""
        return StateMachine(initial_state=States.RUNNING)

    @pytest.fixture
    def metrics_config(self) -> MetricsConfigDTO:
        """Create a metrics config for testing."""
        return MetricsConfigDTO(enabled=True, host="localhost", port=8080)

    @pytest.fixture
    def metrics_server(
        self,
        state_machine: StateMachine,
        metrics_config: MetricsConfigDTO,
    ) -> MetricsServer:
        """Create a MetricsServer instance for testing."""
        return MetricsServer(
            state_machine=state_machine,
            config=metrics_config,
            verbosity=1,
        )

    def test_setup_routes(self, metrics_server: MetricsServer) -> None:
        """Test route setup creates application with correct routes."""
        app = metrics_server._setup_routes()

        assert isinstance(app, Application)

        # Check that routes are registered
        routes = [route.resource.canonical for route in app.router.routes()]
        assert "/" in routes
        assert "/status" in routes

    @pytest.mark.asyncio
    async def test_status_handler_success(self, metrics_server: MetricsServer) -> None:
        """Test successful status endpoint response."""
        request = make_mocked_request("GET", "/status")

        with patch("time.time", return_value=1000.0):
            metrics_server._start_time = 900.0

            mock_datetime = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            with patch("infinity_grid.services.metrics_service.datetime") as mock_dt:
                mock_dt.now.return_value = mock_datetime

                response = await metrics_server._status_handler(request)

        assert response.status == 200
        assert response.content_type == "application/json"

        response_data = json.loads(response.text)
        assert response_data["state"] == "RUNNING"
        assert response_data["uptime_seconds"] == 100.0
        assert response_data["timestamp"] == "2025-01-01T12:00:00+00:00"

    @pytest.mark.asyncio
    async def test_root_handler_success(self, metrics_server: MetricsServer) -> None:
        """Test successful root endpoint response."""
        request = make_mocked_request("GET", "/")

        mock_datetime = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with patch("infinity_grid.services.metrics_service.datetime") as mock_dt:
            mock_dt.now.return_value = mock_datetime

            response = await metrics_server._root_handler(request)

        assert response.status == 200
        assert response.content_type == "application/json"

        response_data = json.loads(response.text)
        assert "endpoints" in response_data
        assert response_data["endpoints"]["/"] == "This help message"
        assert response_data["endpoints"]["/status"] == "Current bot status"
        assert response_data["bot_state"] == "RUNNING"
        assert response_data["timestamp"] == "2025-01-01T12:00:00+00:00"

    @pytest.mark.asyncio
    @patch("infinity_grid.services.metrics_service.web.TCPSite")
    @patch("infinity_grid.services.metrics_service.web.AppRunner")
    async def test_start_success(
        self,
        mock_app_runner: MagicMock,
        mock_tcp_site: MagicMock,
        metrics_server: MetricsServer,
    ) -> None:
        """Test successful server start."""
        mock_runner_instance = AsyncMock()
        mock_app_runner.return_value = mock_runner_instance

        mock_site_instance = AsyncMock()
        mock_tcp_site.return_value = mock_site_instance

        with patch("infinity_grid.services.metrics_service.LOG") as mock_log:
            await metrics_server.start()

        # Verify setup calls
        mock_runner_instance.setup.assert_called_once()
        mock_site_instance.start.assert_called_once()

        # Verify TCP site was created with correct parameters
        mock_tcp_site.assert_called_once_with(mock_runner_instance, "localhost", 8080)

        # Verify internal state
        assert metrics_server._app is not None
        assert metrics_server._runner is mock_runner_instance
        assert metrics_server._site is mock_site_instance

        # Verify logging
        mock_log.debug.assert_called_once()
        mock_log.info.assert_called_once()

    @pytest.mark.asyncio
    @patch("infinity_grid.services.metrics_service.web.TCPSite")
    @patch("infinity_grid.services.metrics_service.web.AppRunner")
    async def test_start_failure(
        self,
        mock_app_runner: MagicMock,
        mock_tcp_site: MagicMock,  # noqa: ARG002
        metrics_server: MetricsServer,
    ) -> None:
        """Test server start failure handling."""
        mock_runner_instance = AsyncMock()
        mock_app_runner.return_value = mock_runner_instance
        mock_runner_instance.setup.side_effect = Exception("Setup failed")

        with pytest.raises(MetricsServerError, match="Failed to start metrics server"):
            await metrics_server.start()

    @pytest.mark.asyncio
    async def test_stop_success(
        self,
        metrics_server: MetricsServer,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test successful server stop."""
        caplog.set_level(logging.INFO)
        mock_site = AsyncMock()
        mock_runner = AsyncMock()
        mock_app = Mock()

        metrics_server._site = mock_site
        metrics_server._runner = mock_runner
        metrics_server._app = mock_app

        await metrics_server.stop()

        mock_site.stop.assert_called_once()
        mock_runner.cleanup.assert_called_once()

        assert metrics_server._site is None
        assert metrics_server._runner is None
        assert metrics_server._app is None
        assert "Metrics server stopped successfully" in caplog.text

    @pytest.mark.asyncio
    async def test_stop_failure(self, metrics_server: MetricsServer) -> None:
        """Test server stop failure handling."""
        mock_site = AsyncMock()
        mock_site.stop.side_effect = Exception("Stop failed")

        metrics_server._site = mock_site

        with pytest.raises(MetricsServerError, match="Failed to stop metrics server"):
            await metrics_server.stop()

    @pytest.mark.asyncio
    async def test_stop_with_no_components(
        self,
        metrics_server: MetricsServer,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test stopping server when no components are initialized."""
        caplog.set_level(logging.INFO)
        metrics_server._site = None
        metrics_server._runner = None
        metrics_server._app = None

        await metrics_server.stop()
        assert "Metrics server stopped successfully" in caplog.text
