# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

from unittest.mock import Mock

import pytest

from infinity_grid.models.configuration import BotConfigDTO


@pytest.fixture
def mock_config() -> BotConfigDTO:
    """Create a mock configuration for testing."""
    config = Mock(spec=BotConfigDTO)
    config.interval = 0.05  # 5% interval
    config.dry_run = False
    config.userref = "123456"
    config.amount_per_grid = 100.0
    config.fee = 0.001  # 0.1% fee
    config.base_currency = "BTC"
    config.quote_currency = "USD"
    config.name = "TestBot"
    return config


@pytest.fixture
def mock_dependencies() -> dict:
    """Create mock dependencies needed for cDCA Strategy initialization."""
    return {"event_bus": Mock(), "state_machine": Mock(), "db": Mock()}
