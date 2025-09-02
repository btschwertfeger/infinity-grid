# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

from logging import getLogger
from typing import Self

import requests

from infinity_grid.interfaces import INotificationChannel

LOG = getLogger(__name__)


class TelegramNotificationChannelAdapter(INotificationChannel):
    """Telegram implementation of the notification channel."""

    def __init__(
        self: Self,
        bot_token: str,
        chat_id: str,
        thread_id: str | None = None,
    ) -> None:
        self.__base_url = f"https://api.telegram.org/bot{bot_token}"
        self.__chat_id = chat_id
        self.__thread_id = thread_id

    def send(self: Self, message: str) -> bool:
        """Send a notification message through Telegram."""
        LOG.debug("Sending Telegram notification: %s", message)
        try:
            response = requests.post(
                f"{self.__base_url}/sendMessage",
                data={
                    "chat_id": self.__chat_id,
                    "text": message,
                    "message_thread_id": self.__thread_id,
                    "parse_mode": "markdown",
                },
                timeout=10,
            )
            return response.status_code == 200
        except Exception as exc:  # noqa: BLE001
            LOG.error("Failed to send Telegram notification", exc_info=exc)
            return False
