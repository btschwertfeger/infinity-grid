# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Unit tests for the notification adapters."""

from unittest.mock import Mock, patch

import pytest
from requests.exceptions import ConnectionError  # noqa: A004

from infinity_grid.adapters.notification import TelegramNotificationChannelAdapter
from infinity_grid.interfaces import INotificationChannel


@pytest.fixture
def telegram_adapter() -> TelegramNotificationChannelAdapter:
    """Create a TelegramNotificationChannelAdapter instance for testing."""
    return TelegramNotificationChannelAdapter("test_token", "test_chat_id")


class TestTelegramNotificationChannelAdapter:
    def test_implements_interface(
        self,
        telegram_adapter: TelegramNotificationChannelAdapter,
    ) -> None:
        """Test that TelegramNotificationChannelAdapter implements INotificationChannel."""
        assert isinstance(telegram_adapter, INotificationChannel)

    def test_initialization(self) -> None:
        """Test proper initialization of TelegramNotificationChannelAdapter."""
        bot_token = "123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"  # noqa: S105
        chat_id = "987654321"
        adapter = TelegramNotificationChannelAdapter(bot_token, chat_id)

        assert adapter._TelegramNotificationChannelAdapter__chat_id == chat_id
        assert (
            adapter._TelegramNotificationChannelAdapter__base_url
            == f"https://api.telegram.org/bot{bot_token}"
        )

    @patch("requests.post")
    def test_send_success(
        self,
        mock_post: Mock,
        telegram_adapter: TelegramNotificationChannelAdapter,
    ) -> None:
        """Test successful message sending."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = telegram_adapter.send("Test message")

        assert result is True
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        assert call_args[1]["data"]["chat_id"] == "test_chat_id"
        assert call_args[1]["data"]["text"] == "Test message"
        assert call_args[1]["data"]["parse_mode"] == "markdown"
        assert call_args[1]["timeout"] == 10

    @patch("requests.post")
    def test_send_failure_bad_status_code(
        self,
        mock_post: Mock,
        telegram_adapter: TelegramNotificationChannelAdapter,
    ) -> None:
        """Test message sending with bad HTTP status code."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        result = telegram_adapter.send("Test message")

        assert result is False

    @patch("requests.post")
    def test_send_connection_error(
        self,
        mock_post: Mock,
        telegram_adapter: TelegramNotificationChannelAdapter,
    ) -> None:
        """Test message sending with connection error."""
        mock_post.side_effect = ConnectionError("Connection failed")

        result = telegram_adapter.send("Test message")

        assert result is False
