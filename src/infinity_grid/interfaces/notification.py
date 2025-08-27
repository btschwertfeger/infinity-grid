# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

from abc import ABC, abstractmethod


class INotificationChannel(ABC):
    """Base interface for notification channels."""

    @abstractmethod
    def send(self, message: str) -> bool:
        """Send a notification message through the channel."""
