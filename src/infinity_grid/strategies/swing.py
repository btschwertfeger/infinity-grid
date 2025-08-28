# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

from decimal import Decimal
from logging import getLogger
from time import sleep
from typing import TYPE_CHECKING, Self

from infinity_grid.strategies.grid_base import GridStrategyBase

if TYPE_CHECKING:
    from infinity_grid.models.exchange import OrderInfoSchema

LOG = getLogger(__name__)


class SwingStrategy(GridStrategyBase):

    def _get_extra_sell_order_price(
        self: Self,
        last_price: float,
    ) -> float:
        """
        Returns the sell order price depending. Also assigns a new highest buy
        price to configuration if there was a new highest buy.
        """
        LOG.debug("Computing the sell order price...")
        order_price: float
        price_of_highest_buy = self._configuration_table.get()["price_of_highest_buy"]
        last_price = float(last_price)

        # Extra sell order when SWING
        # 2x interval above [last close price | price of highest buy]
        order_price = (
            last_price * (1 + self._config.interval) * (1 + self._config.interval)
        )
        if order_price < price_of_highest_buy:
            order_price = (
                price_of_highest_buy
                * (1 + self._config.interval)
                * (1 + self._config.interval)
            )

        return order_price

    def _check_extra_sell_order(self: Self) -> None:
        """
        Checks if an extra sell order can be placed.
        """
        LOG.debug("Checking if extra sell order can be placed...")
        if (
            self._orderbook_table.count(filters={"side": self._exchange_domain.SELL})
            == 0
        ):
            fetched_balances = self._rest_api.get_pair_balance()

            if (
                fetched_balances.base_available * self._ticker
                > self._amount_per_grid_plus_fee
            ):
                order_price = self._get_extra_sell_order_price(
                    last_price=self._ticker,
                )
                self._event_bus.publish(
                    "notification",
                    data={
                        "message": f"ℹ️ {self._config.name}: Placing extra sell order",  # noqa: RUF001
                    },
                )
                self._handle_arbitrage(
                    side=self._exchange_domain.SELL,
                    order_price=order_price,
                )

    def _new_sell_order(
        self: Self,
        order_price: float,
        txid_to_delete: str | None = None,
    ) -> None:
        """Places a new sell order."""
        if self._config.dry_run:
            LOG.info("Dry run, not placing sell order.")
            return

        LOG.debug("Check conditions for placing a sell order...")

        # ======================================================================
        volume: float | None = None
        if txid_to_delete is not None:  # If corresponding buy order filled
            # GridSell always has txid_to_delete set.

            # Add the txid of the corresponding buy order to the unsold buy
            # order txids in order to ensure that the corresponding sell order
            # will be placed - even if placing now fails.
            if not self._unsold_buy_order_txids_table.get(  # type: ignore[no-untyped-call]
                filters={"txid": txid_to_delete},
            ).first():
                self._unsold_buy_order_txids_table.add(
                    txid=txid_to_delete,
                    price=order_price,
                )

            # ==================================================================
            # Get the corresponding buy order in order to retrieve the volume.
            corresponding_buy_order: OrderInfoSchema = (
                self._rest_api.get_order_with_retry(
                    txid=txid_to_delete,
                )
            )

            # In some cases the corresponding buy order is not closed yet and
            # the vol_exec is missing. In this case, the function will be
            # called again after a short delay.
            if (
                corresponding_buy_order.status != self._exchange_domain.CLOSED
                or corresponding_buy_order.vol_exec == 0
            ):
                LOG.warning(
                    "Can't place sell order, since the corresponding buy order"
                    " is not closed yet. Retry in 1 second. (order: %s)",
                    corresponding_buy_order,
                )
                sleep(1)
                self._new_sell_order(
                    order_price=order_price,
                    txid_to_delete=txid_to_delete,
                )
                return

        order_price = float(
            self._rest_api.truncate(
                amount=order_price,
                amount_type="price",
            ),
        )

        # Respect the fee to not reduce the quote currency over time, while
        # accumulating the base currency.
        volume = float(
            self._rest_api.truncate(
                amount=Decimal(self._config.amount_per_grid)
                / (Decimal(order_price) * (1 - (2 * Decimal(self._config.fee)))),
                amount_type="volume",
            ),
        )

        # ======================================================================
        # Check if there is enough base currency available for selling.
        fetched_balances = self._rest_api.get_pair_balance()
        if fetched_balances.base_available >= volume:
            # Place new sell order, append id to pending list, and delete
            # corresponding buy order from local orderbook.
            LOG.info(
                "Placing order to sell %s %s @ %s %s.",
                volume,
                self._config.base_currency,
                order_price,
                self._config.quote_currency,
            )

            placed_order = self._rest_api.create_order(
                ordertype="limit",
                side=self._exchange_domain.SELL,
                volume=volume,
                price=order_price,
                userref=self._config.userref,
                validate=self._config.dry_run,
            )

            self._pending_txids_table.add(placed_order.txid)

            if txid_to_delete is not None:
                # Other than with buy orders, we can only delete the
                # corresponding buy order if the sell order was placed.
                self._orderbook_table.remove(filters={"txid": txid_to_delete})
                self._unsold_buy_order_txids_table.remove(txid=txid_to_delete)

            self._assign_order_by_txid(txid=placed_order.txid)
            return

        # ======================================================================
        # Not enough funds to sell
        message = f"⚠️ {self._config.name} ({self._rest_api.rest_symbol})\n"
        message += f"├ Not enough {self._config.base_currency}\n"
        message += f"├ to sell {volume} {self._config.base_currency}\n"
        message += f"└ for {order_price} {self._config.quote_currency}"

        self._event_bus.publish("notification", data={"message": message})
        LOG.warning("Current balances: %s", fetched_balances)

        if txid_to_delete is not None:
            # TODO: Check if this is appropriate or not
            #       Added logging statement to monitor occurrences
            # ... This would only be the case for GridHODL and SWING, while
            # those should always have enough base currency available... but
            # lets check this for a while.
            LOG.warning(
                "Not enough funds to place sell order for txid %s",
                txid_to_delete,
            )
            self._orderbook_table.remove(filters={"txid": txid_to_delete})
