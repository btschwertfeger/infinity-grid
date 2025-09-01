# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

import pytest

from infinity_grid.models.configuration import NotificationConfigDTO, TelegramConfigDTO


@pytest.fixture(scope="session")
def notification_config() -> NotificationConfigDTO:
    return NotificationConfigDTO(telegram=TelegramConfigDTO(token=None, chat_id=None))
