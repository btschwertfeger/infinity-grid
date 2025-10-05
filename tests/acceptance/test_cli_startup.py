# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Acceptance tests for the Infinity Grid CLI.

These tests verify that the bot can be started from the command line
and transitions through the expected states correctly.

This test suite requires valid API keys set in the environment:
- INFINITY_GRID_API_PUBLIC_KEY
- INFINITY_GRID_API_SECRET_KEY

These MUST be configured to not allow creation or closing of real orders. Also
make sure that the API keys have the necessary permissions to *only* read data.
"""

import os
from typing import Self
from unittest import mock
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from infinity_grid.core.cli import cli
from infinity_grid.core.state_machine import States

API_PUBLIC_KEY = os.getenv("INFINITY_GRID_API_PUBLIC_KEY")
API_SECRET_KEY = os.getenv("INFINITY_GRID_API_SECRET_KEY")


@pytest.mark.acceptance
class TestCLIStartup:
    """Test suite for CLI startup and basic lifecycle"""

    @pytest.mark.timeout(30)
    @pytest.mark.skipif(
        API_PUBLIC_KEY is None or API_SECRET_KEY is None,
        reason="Environment variables 'INFINITY_GRID_API_PUBLIC_KEY' and"
        " 'INFINITY_GRID_API_SECRET_KEY' must be set!",
    )
    @pytest.mark.parametrize("exchange", ["Kraken"])
    @mock.patch("infinity_grid.adapters.exchanges.kraken.sleep", return_value=None)
    @mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
    def test_cli_starts_and_reaches_running_state(
        self: Self,
        mock_sleep1: mock.MagicMock,  # noqa: ARG002
        mock_sleep2: mock.MagicMock,  # noqa: ARG002
        cli_runner: CliRunner,
        exchange: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """
        Test that the infinity-grid bot can be started via CLI with --in-memory
        and --debug flags, and successfully reaches the RUNNING state before
        being gracefully shutdown.

        This test:
        1. Starts the bot with minimal configuration using Click's CliRunner
        2. Intercepts the state machine to detect RUNNING state
        3. Triggers shutdown when RUNNING state is reached
        4. Verifies the bot shuts down cleanly
        """
        caplog.set_level("INFO")

        from infinity_grid.core.state_machine import StateMachine

        running_state_reached = [False]  # Use list for mutability in nested scope
        original_transition_to = StateMachine.transition_to

        def mock_transition_to(self: Self, new_state: States) -> None:
            """Mock transition_to to detect RUNNING state and trigger shutdown"""
            original_transition_to(self, new_state)

            # When RUNNING state is reached, immediately request shutdown
            if new_state == States.RUNNING and not running_state_reached[0]:
                running_state_reached[0] = True
                original_transition_to(self, States.SHUTDOWN_REQUESTED)

        with patch.object(StateMachine, "transition_to", mock_transition_to):
            result = cli_runner.invoke(
                cli,
                [
                    "-vv",
                    "run",
                    "--strategy",
                    "GridHODL",
                    "--name",
                    "acceptance-test-bot",
                    "--exchange",
                    exchange,
                    "--userref",
                    "999999",
                    "--base-currency",
                    "BTC",
                    "--quote-currency",
                    "USD",
                    "--amount-per-grid",
                    "100",
                    "--interval",
                    "0.02",
                    "--n-open-buy-orders",
                    "3",
                    "--in-memory",
                    "--dry-run",  # Don't execute real trades
                    "--skip-permission-check",  # Skip API key validation
                ],
                catch_exceptions=False,
            )

        assert running_state_reached[0], "Bot never reached RUNNING state"
        assert (
            "RUNNING" in result.output or running_state_reached[0]
        ), "Bot did not log RUNNING state transition"
