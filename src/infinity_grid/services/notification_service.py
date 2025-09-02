# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

from logging import getLogger
from typing import Self

from infinity_grid.interfaces import INotificationChannel
from infinity_grid.models.configuration import NotificationConfigDTO

LOG = getLogger(__name__)


class NotificationService:
    """Service for sending notifications through configured channels."""

    def __init__(self: Self, config: NotificationConfigDTO) -> None:
        self.__channels: list[INotificationChannel] = []
        self.__config = config
        self._setup_channels_from_config()

    def _setup_channels_from_config(self: Self) -> None:
        """Set up notification channels from the loaded config."""
        if self.__config.telegram and self.__config.telegram.enabled:
            self.add_telegram_channel(
                token=self.__config.telegram.token,
                chat_id=self.__config.telegram.chat_id,
                thread_id=self.__config.telegram.thread_id,
            )

    def add_channel(self: Self, channel: INotificationChannel) -> None:
        """Add a notification channel to the service."""
        self.__channels.append(channel)

    def add_telegram_channel(
        self: Self,
        token: str,
        chat_id: str,
        thread_id: str | None = None,
    ) -> None:
        """Convenience method to add a Telegram notification channel."""
        from infinity_grid.adapters.notification import (  # pylint: disable=import-outside-toplevel # noqa: PLC0415
            TelegramNotificationChannelAdapter,
        )

        self.add_channel(
            TelegramNotificationChannelAdapter(token, chat_id, thread_id),
        )

    def notify(self: Self, message: str) -> bool:
        """Send a notification through all configured channels."""
        if not self.__channels:
            return False

        LOG.info("Sending notification: %s", message)

        message_sent = False
        for channel in self.__channels:
            if channel.send(message):
                message_sent = True

        return message_sent

    def on_notification(self: Self, data: dict) -> None:
        """Handle a notification event."""
        self.notify(data["message"])
