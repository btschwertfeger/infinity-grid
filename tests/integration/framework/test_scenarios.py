# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Reusable test scenarios for integration testing.

This module contains predefined test scenarios that can be executed
across different exchanges and strategies, ensuring consistent testing
approaches and reducing code duplication.
"""

import logging

from .base_test_manager import BaseIntegrationTestManager

LOG = logging.getLogger(__name__)


class IntegrationTestScenarios:
    """
    Collection of reusable test scenarios for trading strategies.

    These scenarios are exchange-agnostic and can be used with any
    implementation of BaseIntegrationTestManager.
    """

    def __init__(self, test_manager: BaseIntegrationTestManager) -> None:
        self.manager = test_manager
