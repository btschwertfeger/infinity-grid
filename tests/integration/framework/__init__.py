# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Exchange-agnostic integration testing framework.

This module provides base classes and utilities for creating integration tests
that can work with multiple exchanges while maintaining consistency and reducing
code duplication.
"""

from .base_test_manager import (
    BaseIntegrationTestManager,
    ExchangeTestConfig,
    MockExchangeAPI,
)
from .test_scenarios import IntegrationTestScenarios

__all__ = [
    "BaseIntegrationTestManager",
    "ExchangeTestConfig",
    "IntegrationTestScenarios",
    "MockExchangeAPI",
]
