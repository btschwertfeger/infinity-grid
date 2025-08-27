# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Test module for notification service.

This module contains focused tests for the NotificationService class,
testing the core functionality and channel management.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from infinity_grid.interfaces import INotificationChannel
from infinity_grid.models.configuration import NotificationConfigDTO, TelegramConfigDTO
from infinity_grid.services.notification_service import NotificationService

TOKEN = "123:abdsljhbfadshkjfgbakrjhfbadjfhbac"  # noqa: S105
CHAT_ID = "456"


class TestNotificationService:
    """Test cases for NotificationService"""

    def test_init_with_disabled_telegram(self) -> None:
        """Test initialization with disabled telegram config"""
        config = NotificationConfigDTO(
            telegram=TelegramConfigDTO(token=None, chat_id=None),
        )
        service = NotificationService(config)

        # Should have no channels when telegram is disabled
        assert service.notify("test") is False

    @patch(
        "infinity_grid.adapters.notification.TelegramNotificationChannelAdapter",
    )
    def test_init_with_enabled_telegram(self, mock_telegram_adapter: MagicMock) -> None:
        """Test initialization with enabled telegram config"""
        config = NotificationConfigDTO(
            telegram=TelegramConfigDTO(token=TOKEN, chat_id=CHAT_ID),
        )
        service = NotificationService(config)

        # Should create telegram adapter when enabled
        mock_telegram_adapter.assert_called_once_with(TOKEN, CHAT_ID)

    def test_add_channel(self) -> None:
        """Test adding a notification channel"""
        config = NotificationConfigDTO(
            telegram=TelegramConfigDTO(token=None, chat_id=None),
        )
        service = NotificationService(config)

        # Mock channel
        mock_channel = Mock(spec=INotificationChannel)
        mock_channel.send.return_value = True

        service.add_channel(mock_channel)

        # Should now be able to send notifications
        assert service.notify("test message") is True
        mock_channel.send.assert_called_once_with("test message")

    @patch(
        "infinity_grid.adapters.notification.TelegramNotificationChannelAdapter",
    )
    def test_add_telegram_channel(self, mock_telegram_adapter: MagicMock) -> None:
        """Test adding telegram channel via convenience method"""
        config = NotificationConfigDTO(
            telegram=TelegramConfigDTO(token=None, chat_id=None),
        )
        service = NotificationService(config)

        service.add_telegram_channel("token123", "chat456")

        mock_telegram_adapter.assert_called_once_with("token123", "chat456")

    def test_notify_no_channels(self) -> None:
        """Test notification when no channels are configured"""
        config = NotificationConfigDTO(
            telegram=TelegramConfigDTO(token=None, chat_id=None),
        )
        service = NotificationService(config)

        result = service.notify("test message")

        assert result is False

    def test_notify_single_channel_success(self) -> None:
        """Test notification with single successful channel"""
        config = NotificationConfigDTO(
            telegram=TelegramConfigDTO(token=None, chat_id=None),
        )
        service = NotificationService(config)

        mock_channel = Mock(spec=INotificationChannel)
        mock_channel.send.return_value = True
        service.add_channel(mock_channel)

        result = service.notify("test message")

        assert result is True
        mock_channel.send.assert_called_once_with("test message")

    def test_notify_single_channel_failure(self) -> None:
        """Test notification with single failing channel"""
        config = NotificationConfigDTO(
            telegram=TelegramConfigDTO(token=None, chat_id=None),
        )
        service = NotificationService(config)

        mock_channel = Mock(spec=INotificationChannel)
        mock_channel.send.return_value = False
        service.add_channel(mock_channel)

        result = service.notify("test message")

        assert result is False
        mock_channel.send.assert_called_once_with("test message")

    def test_notify_multiple_channels_mixed_results(self) -> None:
        """Test notification with multiple channels having mixed success/failure"""
        config = NotificationConfigDTO(
            telegram=TelegramConfigDTO(token=None, chat_id=None),
        )
        service = NotificationService(config)

        # Add successful channel
        success_channel = Mock(spec=INotificationChannel)
        success_channel.send.return_value = True
        service.add_channel(success_channel)

        # Add failing channel
        fail_channel = Mock(spec=INotificationChannel)
        fail_channel.send.return_value = False
        service.add_channel(fail_channel)

        result = service.notify("test message")

        # Should return True if at least one channel succeeds
        assert result is True
        success_channel.send.assert_called_once_with("test message")
        fail_channel.send.assert_called_once_with("test message")

    def test_notify_multiple_channels_all_fail(self) -> None:
        """Test notification when all channels fail"""
        config = NotificationConfigDTO(
            telegram=TelegramConfigDTO(token=None, chat_id=None),
        )
        service = NotificationService(config)

        # Add two failing channels
        fail_channel1 = Mock(spec=INotificationChannel)
        fail_channel1.send.return_value = False
        service.add_channel(fail_channel1)

        fail_channel2 = Mock(spec=INotificationChannel)
        fail_channel2.send.return_value = False
        service.add_channel(fail_channel2)

        result = service.notify("test message")

        assert result is False
        fail_channel1.send.assert_called_once_with("test message")
        fail_channel2.send.assert_called_once_with("test message")

    @patch("infinity_grid.services.notification_service.LOG")
    def test_notify_logs_message(self, mock_log: MagicMock) -> None:
        """Test that notify logs the message being sent"""
        config = NotificationConfigDTO(
            telegram=TelegramConfigDTO(token=None, chat_id=None),
        )
        service = NotificationService(config)

        mock_channel = Mock(spec=INotificationChannel)
        mock_channel.send.return_value = True
        service.add_channel(mock_channel)

        service.notify("important message")

        mock_log.info.assert_called_once_with(
            "Sending notification: %s",
            "important message",
        )

    def test_on_notification(self) -> None:
        """Test on_notification event handler"""
        config = NotificationConfigDTO(
            telegram=TelegramConfigDTO(token=None, chat_id=None),
        )
        service = NotificationService(config)

        mock_channel = Mock(spec=INotificationChannel)
        mock_channel.send.return_value = True
        service.add_channel(mock_channel)

        # Call event handler
        service.on_notification({"message": "event message"})

        # Should extract message from data and call notify
        mock_channel.send.assert_called_once_with("event message")

    def test_on_notification_missing_message_key(self) -> None:
        """Test on_notification with missing message key"""
        config = NotificationConfigDTO(
            telegram=TelegramConfigDTO(token=None, chat_id=None),
        )
        service = NotificationService(config)

        # Should raise KeyError when message key is missing
        with pytest.raises(KeyError):
            service.on_notification({"data": "no message key"})

    @patch(
        "infinity_grid.adapters.notification.TelegramNotificationChannelAdapter",
    )
    def test_setup_channels_from_config_enabled(
        self,
        mock_telegram_adapter: MagicMock,
    ) -> None:
        """
        Test that _setup_channels_from_config creates telegram channel when
        enabled
        """

        config = NotificationConfigDTO(
            telegram=TelegramConfigDTO(token=TOKEN, chat_id=CHAT_ID),
        )

        # This should trigger _setup_channels_from_config in __init__
        NotificationService(config)

        mock_telegram_adapter.assert_called_once_with(TOKEN, CHAT_ID)

    def test_setup_channels_from_config_disabled(self) -> None:
        """Test that _setup_channels_from_config doesn't create channels when disabled"""
        config = NotificationConfigDTO(
            telegram=TelegramConfigDTO(token=None, chat_id=None),
        )

        service = NotificationService(config)

        # Should have no channels
        assert service.notify("test") is False
