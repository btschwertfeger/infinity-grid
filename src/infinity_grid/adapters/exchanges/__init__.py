# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Exchange adapters package."""

# Import all exchange adapters to trigger auto-registration
from infinity_grid.adapters.exchanges import kraken

__all__ = ["kraken"]
