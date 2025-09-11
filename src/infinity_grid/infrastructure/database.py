# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Module implementing the database connection and handling of interactions."""

from copy import deepcopy
from importlib.metadata import version
from logging import getLogger
from typing import Any, Self

from sqlalchemy import Boolean, Column, Float, Integer, String, Table, func, select
from sqlalchemy.engine.result import MappingResult
from sqlalchemy.engine.row import RowMapping

from infinity_grid.models.exchange import OrderInfoSchema
from infinity_grid.services.database import DBConnect

LOG = getLogger(__name__)


class Orderbook:
    """Table containing the orderbook data."""

    def __init__(self: Self, userref: int, db: DBConnect) -> None:
        LOG.debug("Initializing the orderbook table...")
        self.__db = db
        self.__userref = userref
        self.__table = Table(
            "orderbook",
            db.metadata,
            Column("id", Integer, primary_key=True),
            Column("userref", Integer, nullable=False),
            Column("txid", String, nullable=False),
            Column("symbol", String, nullable=False),
            Column("side", String, nullable=False),
            Column("price", Float, nullable=False),
            Column("volume", Float, nullable=False),
        )

    def add(self: Self, order: OrderInfoSchema) -> None:
        """Add an order to the orderbook."""
        LOG.debug("Adding order to the orderbook: %s", order)
        self.__db.add_row(
            self.__table,
            userref=self.__userref,
            txid=order.txid,
            symbol=order.pair,
            side=order.side,
            price=order.price,
            volume=order.vol,
        )

    def get_orders(
        self: Self,
        filters: dict | None = None,
        exclude: dict | None = None,
        order_by: tuple[str, str] | None = None,
        limit: int | None = None,
    ) -> MappingResult:
        """Get orders from the orderbook."""
        if not filters:
            filters = {}
        filters |= {"userref": self.__userref}

        LOG.debug(
            "Getting orders from the orderbook with filter: %s, exclude: %s, order_by: %s, limit: %s",
            filters,
            exclude,
            order_by,
            limit,
        )
        return self.__db.get_rows(
            self.__table,
            filters=filters,
            exclude=exclude,
            order_by=order_by,
            limit=limit,
        )

    def remove(self: Self, filters: dict) -> None:
        """Remove orders from the orderbook."""
        if not filters:
            raise ValueError("Filters required for removal from orderbook")
        filters |= {"userref": self.__userref}
        LOG.debug("Removing orders from the orderbook: %s", filters)
        self.__db.delete_row(self.__table, filters=filters)

    def update(self: Self, updates: OrderInfoSchema) -> None:
        """
        Update order in the orderbook.

        In case one manually modifies the order. This is not recommended!
        """
        LOG.debug("Updating order in the orderbook: %s", updates)

        self.__db.update_row(
            self.__table,
            filters={"userref": self.__userref, "txid": updates.txid},
            updates={
                "side": updates.side,
                "price": updates.price,
                "volume": updates.vol,
            },
        )

    def count(
        self: Self,
        filters: dict | None = None,
        exclude: dict | None = None,
    ) -> int:
        """Count orders in the orderbook."""
        if not filters:
            filters = {}
        filters |= {"userref": self.__userref}

        LOG.debug(
            "Counting orders in the orderbook with filters: %s and exclude: %s",
            filters,
            exclude,
        )

        query = (
            select(func.count())  # pylint: disable=not-callable
            .select_from(self.__table)
            .where(
                *(self.__table.c[column] == value for column, value in filters.items()),
            )
        )
        if exclude:
            query = query.where(
                *(self.__table.c[column] != value for column, value in exclude.items()),
            )
        return self.__db.session.execute(query).scalar()  # type: ignore[no-any-return]


class Configuration:
    """Table containing information about the bots config."""

    def __init__(self: Self, userref: int, db: DBConnect) -> None:
        LOG.debug("Initializing the configuration table...")
        self.__db = db
        self.__userref = userref
        self.__cache: dict[frozenset, Any] = {}
        self.__table = Table(
            "configuration",
            self.__db.metadata,
            Column("id", Integer, primary_key=True),
            Column("userref", Integer, nullable=False),
            Column("version", String, nullable=False),
            Column("vol_of_unfilled_remaining", Float, nullable=False, default=0),
            Column(
                "vol_of_unfilled_remaining_max_price",
                Float,
                nullable=False,
                default=0,
            ),
            Column("price_of_highest_buy", Float, nullable=False, default=0),
            Column("amount_per_grid", Float),
            Column("interval", Float),
            Column("trailing_stop_profit", Float, nullable=True),
            extend_existing=True,
        )

        # Create if not exist
        self.__table.create(bind=self.__db.engine, checkfirst=True)

        current_version = version("infinity-grid")

        # Add initial values
        if not self.__db.get_rows(
            self.__table,
            filters={"userref": self.__userref},
        ).fetchone():  # type: ignore[no-untyped-call]
            self.__db.add_row(
                self.__table,
                userref=self.__userref,
                version=current_version,
            )
        # Check if version needs to be updated
        elif (config := self.get()) and config.version != current_version:  # type: ignore[attr-defined]
            LOG.info(
                "Updating infinity-grid version in database from %s to %s",
                config.version,  # type: ignore[attr-defined]
                current_version,
            )
            self.update(updates={"version": current_version})

    def get(self: Self, filters: dict | None = None) -> RowMapping:
        """
        Get configuration from the table.

        Uses cache if available to avoid unnecessary database queries.

        Returns:
            RowMapping with the following attributes:
                - id: Primary key
                - userref: User reference ID
                - version: Version of the software
                - vol_of_unfilled_remaining: Volume of unfilled orders remaining
                - vol_of_unfilled_remaining_max_price: Max price of unfilled volume remaining
                - price_of_highest_buy: Price of the highest buy order
                - amount_per_grid: Amount allocated per grid
                - interval: Interval setting
        """
        if not filters:
            filters = {}
        filters |= {"userref": self.__userref}

        LOG.debug(
            "Getting configuration from cache or table 'configuration' with filter: %s",
            filters,
        )

        if (cache_key := frozenset((k, v) for k, v in filters.items())) in self.__cache:
            LOG.debug("Using cached configuration data")
            return deepcopy(self.__cache[cache_key])  # type: ignore[no-any-return]

        LOG.debug("Cache miss, fetching from database")

        if result := self.__db.get_rows(self.__table, filters=filters):
            config = next(result)
            self.__cache[cache_key] = config
            return deepcopy(config)  # type: ignore[no-any-return]

        raise ValueError(f"No configuration found for passed {filters=}!")

    def update(self: Self, updates: dict) -> None:
        """
        Update configuration in the table.

        Invalidates the cache to ensure fresh data on next get().
        """
        LOG.debug("Updating configuration in the table: %s", updates)
        self.__db.update_row(
            self.__table,
            filters={"userref": self.__userref},
            updates=updates,
        )
        self.__cache = {}


class UnsoldBuyOrderTXIDs:
    """
    Table containing information about future sell orders. Entries are added
    before placing a new sell order in order to not miss the placement in case
    placing fails.

    If the placement succeeds, the entry gets deleted from this table.
    """

    def __init__(self: Self, userref: int, db: DBConnect) -> None:
        LOG.debug("Initializing the UnsoldBuyOrderTXIDs table...")
        self.__db = db
        self.__userref = userref
        self.__table = Table(
            "unsold_buy_order_txids",
            self.__db.metadata,
            Column("id", Integer, primary_key=True),
            Column("userref", Integer, nullable=False),
            Column("txid", String, nullable=False),  # corresponding buy order
            Column("price", Float, nullable=False),  # price at which to sell
        )

    def add(self: Self, txid: str, price: float) -> None:
        """Add a missed sell order to the table."""
        LOG.debug(
            "Adding unsold buy order txid to the 'unsold_buy_order_txids' table: %s",
            txid,
        )
        self.__db.add_row(
            self.__table,
            userref=self.__userref,
            txid=txid,
            price=price,
        )

    def remove(self: Self, txid: str) -> None:
        """Remove txid from the table."""
        LOG.debug(
            "Removing unsold buy order txid from the 'unsold_buy_order_txids'"
            " with filter: %s",
            filters := {"userref": self.__userref, "txid": txid},
        )
        self.__db.delete_row(self.__table, filters=filters)

    def get(self: Self, filters: dict | None = None) -> MappingResult:
        """Retrieve unsold buy order txids from the table."""
        if not filters:
            filters = {}
        filters |= {"userref": self.__userref}
        LOG.debug(
            "Retrieving unsold buy order txids from the"
            " 'unsold_buy_order_txids' table with filters: %s",
            filters,
        )
        return self.__db.get_rows(self.__table, filters=filters)

    def count(self: Self, filters: dict | None = None) -> int:
        """Count unsold buy order txids from the table."""
        if not filters:
            filters = {}
        filters |= {"userref": self.__userref}

        LOG.debug(
            "Count unsold buy order txids from the table unsold_buy_order_txids"
            " table with filters: %s",
            filters,
        )

        query = (
            select(func.count())  # pylint: disable=not-callable
            .select_from(self.__table)
            .where(
                *(self.__table.c[column] == value for column, value in filters.items()),
            )
        )
        return self.__db.session.execute(query).scalar()  # type: ignore[no-any-return]


class PendingTXIDs:
    """
    Table containing pending TXIDs. TXIDs are pending for the time from being
    placed to processed by an exchange. Usually an order gets placed, the TXID
    is returned and stored in this table. Then the algorithm fetches this
    'pending' TXID to retrieve the full order information in order to add these
    to the local orderbook. After that, the TXID gets removed from this table.
    """

    def __init__(self: Self, userref: int, db: DBConnect) -> None:
        LOG.debug("Initializing the PendingIXIDs table...")
        self.__db = db
        self.__userref = userref
        self.__table = Table(
            "pending_txids",
            self.__db.metadata,
            Column("id", Integer, primary_key=True),
            Column("userref", Integer, nullable=False),
            Column("txid", String, nullable=False),
        )

    def get(self: Self, filters: dict | None = None) -> MappingResult:
        """Get pending orders from the table."""
        if not filters:
            filters = {}
        filters |= {"userref": self.__userref}

        LOG.debug(
            "Getting orders from the 'pending_txids' table with filter: %s",
            filters,
        )

        return self.__db.get_rows(self.__table, filters=filters)

    def add(self: Self, txid: str) -> None:
        """Add a pending order to the table."""
        LOG.debug(
            "Adding an order to the 'pending_txids' table: '%s'",
            txid,
        )
        self.__db.add_row(self.__table, userref=self.__userref, txid=txid)

    def remove(self: Self, txid: str) -> None:
        """Remove a pending order from the table."""

        LOG.debug(
            "Removing order from the 'pending_txids' table with filters: %s",
            filters := {"userref": self.__userref, "txid": txid},
        )
        self.__db.delete_row(self.__table, filters=filters)

    def count(self: Self, filters: dict | None = None) -> int:
        """Count pending orders in the table."""
        if not filters:
            filters = {}
        filters |= {"userref": self.__userref}

        LOG.debug(
            "Counting orders in 'pending_txids' table with filter: %s",
            filters,
        )

        query = (
            select(func.count())  # pylint: disable=not-callable
            .select_from(self.__table)
            .where(
                *(self.__table.c[column] == value for column, value in filters.items()),
            )
        )
        return self.__db.session.execute(query).scalar()  # type: ignore[no-any-return]


class FutureOrders:
    """
    Table containing orders that need to be placed as soon as possible.
    """

    def __init__(self: Self, userref: int, db: DBConnect) -> None:
        LOG.debug("Initializing the 'future_orders' table...")
        self.__db = db
        self.__userref = userref
        self.__table = Table(
            "future_orders",
            self.__db.metadata,
            Column("id", Integer, primary_key=True),
            Column("userref", Integer, nullable=False),
            Column("price", Float, nullable=False),
        )

        # Create the table if it doesn't exist
        self.__table.create(bind=self.__db.engine, checkfirst=True)

    def get(self: Self, filters: dict | None = None) -> MappingResult:
        """Get row from the table."""
        if not filters:
            filters = {}
        filters |= {"userref": self.__userref}

        LOG.debug(
            "Getting rows from the 'future_orders' table with filter: %s",
            filters,
        )

        return self.__db.get_rows(self.__table, filters=filters)

    def add(self: Self, price: float) -> None:
        """Add an order to the table."""
        LOG.debug("Adding a order to the 'future_orders' table: price: %s", price)
        self.__db.add_row(self.__table, userref=self.__userref, price=price)

    def remove_by_price(self: Self, price: float) -> None:
        """Remove a row from the table."""
        LOG.debug(
            "Removing rows from the 'future_orders' table with filters: %s",
            filters := {"userref": self.__userref, "price": price},
        )
        self.__db.delete_row(self.__table, filters=filters)


class TSPState:
    """
    Table for tracking Trailing Stop Profit state independently of orders.
    This table maintains TSP state even when orders are canceled and replaced,
    ensuring continuity of TSP tracking.
    """

    def __init__(
        self: Self,
        userref: int,
        db: DBConnect,
        tsp_percentage: float = 0.01,
    ) -> None:
        LOG.debug("Initializing the 'tsp_state' table...")
        self.__db = db
        self.__userref = userref
        self.__tsp_percentage = tsp_percentage
        self.__table = Table(
            "tsp_state",
            self.__db.metadata,
            Column("id", Integer, primary_key=True),
            Column("userref", Integer, nullable=False),
            Column(
                "original_buy_txid",
                String,
                nullable=False,
            ),  # UNIQUE KEY per position
            Column("original_buy_price", Float, nullable=False),  # Never changes
            Column(
                "current_stop_price",
                Float,
                nullable=False,
            ),  # Updates as trailing stop moves
            Column(
                "tsp_active",
                Boolean,
                default=False,
            ),  # Whether TSP is currently active
            Column(
                "current_sell_order_txid",
                String,
                nullable=True,
            ),  # Updates when orders shift
        )

        self.__table.create(bind=self.__db.engine, checkfirst=True)

    def add(
        self: Self,
        original_buy_txid: str,
        original_buy_price: float,
        initial_stop_price: float,
        sell_order_txid: str,
    ) -> None:
        """Add a new TSP tracking entry."""
        LOG.debug(
            "Adding TSP state: buy_txid=%s, buy_price=%s, stop_price=%s, sell_txid=%s",
            original_buy_txid,
            original_buy_price,
            initial_stop_price,
            sell_order_txid,
        )
        self.__db.add_row(
            self.__table,
            userref=self.__userref,
            original_buy_txid=original_buy_txid,
            original_buy_price=original_buy_price,
            current_stop_price=initial_stop_price,
            tsp_active=False,
            current_sell_order_txid=sell_order_txid,
        )

    def update_sell_order_txid(self: Self, old_txid: str | None, new_txid: str) -> None:
        """Update the sell order TXID when order is replaced."""
        LOG.debug("Updating TSP sell order TXID from %s to %s", old_txid, new_txid)

        if old_txid is None:
            # Special case: updating from None (unlinked state)
            # We need to find the record and update it, but we can't filter by None
            # This is handled in the calling code with a direct update
            return

        self.__db.update_row(
            self.__table,
            filters={"userref": self.__userref, "current_sell_order_txid": old_txid},
            updates={"current_sell_order_txid": new_txid},
        )

    def update_sell_order_txid_by_buy_txid(
        self: Self,
        original_buy_txid: str,
        new_sell_txid: str,
    ) -> None:
        """Update sell order TXID for a specific buy TXID."""
        LOG.debug(
            "Updating sell order TXID for buy %s to %s",
            original_buy_txid,
            new_sell_txid,
        )
        self.__db.update_row(
            self.__table,
            filters={"userref": self.__userref, "original_buy_txid": original_buy_txid},
            updates={"current_sell_order_txid": new_sell_txid},
        )

    def activate_tsp(self: Self, original_buy_txid: str, current_price: float) -> None:
        """Activate TSP for a specific position."""
        LOG.debug(
            "Activating TSP for buy_txid %s at current price %s",
            original_buy_txid,
            current_price,
        )
        self.__db.update_row(
            self.__table,
            filters={"userref": self.__userref, "original_buy_txid": original_buy_txid},
            updates={
                "tsp_active": True,
                "current_stop_price": current_price * (1 - self.__get_tsp_percentage()),
            },
        )

    def update_trailing_stop(
        self: Self,
        original_buy_txid: str,
        current_price: float,
    ) -> None:
        """Update trailing stop level if price has moved higher."""
        LOG.debug(
            "Updating trailing stop for buy_txid=%s: new_stop=%s, highest=%s",
            original_buy_txid,
            new_stop_price := current_price * (1 - self.__get_tsp_percentage()),
            current_price,
        )
        self.__db.update_row(
            self.__table,
            filters={"userref": self.__userref, "original_buy_txid": original_buy_txid},
            updates={
                "current_stop_price": new_stop_price,
            },
        )

    def get_by_buy_txid(self: Self, original_buy_txid: str) -> RowMapping | None:
        """Get TSP state for a specific buy TXID."""
        return self.__db.get_rows(
            self.__table,
            filters={"userref": self.__userref, "original_buy_txid": original_buy_txid},
        ).fetchone()

    def get_by_sell_txid(self: Self, sell_txid: str) -> RowMapping | None:
        """Get TSP state by current sell order TXID."""
        return self.__db.get_rows(
            self.__table,
            filters={"userref": self.__userref, "current_sell_order_txid": sell_txid},
        ).fetchone()

    def get_all_active(self: Self) -> MappingResult:
        """Get all active TSP states."""
        return self.__db.get_rows(
            self.__table,
            filters={"userref": self.__userref, "tsp_active": True},
        )

    def remove_by_buy_txid(self: Self, original_buy_txid: str) -> None:
        """Remove TSP state when position is closed."""
        LOG.debug("Removing TSP state for buy TXID %s", original_buy_txid)
        self.__db.delete_row(
            self.__table,
            filters={"userref": self.__userref, "original_buy_txid": original_buy_txid},
        )

    def remove_by_txid(self: Self, txid: str) -> None:
        """Remove TSP state by sell order TXID."""
        LOG.debug("Removing TSP state for sell order %s", txid)
        self.__db.delete_row(
            self.__table,
            filters={"userref": self.__userref, "current_sell_order_txid": txid},
        )

    def __get_tsp_percentage(self: Self) -> float:
        """Get TSP percentage from configuration."""
        return self.__tsp_percentage
