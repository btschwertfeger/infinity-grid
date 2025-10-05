# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

import pytest
from click.testing import CliRunner

from infinity_grid.models.configuration import DBConfigDTO


@pytest.fixture(scope="session")
def db_config() -> DBConfigDTO:
    return DBConfigDTO(
        user="test_user",
        password="test_password",
        host="localhost",
        port=5432,
        database="test_db",
        sqlite_file=":memory:",
    )


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()
