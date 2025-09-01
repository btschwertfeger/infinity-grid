# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

from logging import getLogger
from typing import Self

from infinity_grid.strategies.grid_base import GridStrategyBase

LOG = getLogger(__name__)


class CDCAStrategy(GridStrategyBase):

    def _get_sell_order_price(
        self: Self,
        last_price: float,
    ) -> float:
        """Returns the order price for the next sell order."""
        LOG.debug("cDCA strategy does not place sell orders.")

        if (last_price := float(last_price)) > self._configuration_table.get()[
            "price_of_highest_buy"
        ]:
            self._configuration_table.update({"price_of_highest_buy": last_price})
        return None

    def _check_extra_sell_order(self: Self) -> None:
        """Not applicable for cDCA strategy."""

    def _new_sell_order(
        self: Self,
        order_price: float,  # noqa: ARG002
        txid_to_delete: str | None = None,
    ) -> None:
        """Places a new sell order."""
        if self._config.dry_run:
            LOG.info("Dry run, not placing sell order.")
            return

        LOG.debug("cDCA strategy, not placing sell order.")
        if txid_to_delete is not None:
            self._orderbook_table.remove(filters={"txid": txid_to_delete})
