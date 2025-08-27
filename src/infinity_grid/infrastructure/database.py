# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Module implementing the database connection and handling of interactions."""

from datetime import datetime
from importlib.metadata import version
from logging import getLogger
from typing import Self

from sqlalchemy import Column, DateTime, Float, Integer, String, Table, func, select
from sqlalchemy.engine.result import MappingResult

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
        LOG.debug(
            "Getting orders from the orderbook with filters: %s, exclude: %s, order_by: %s, limit: %s",
            filters,
            exclude,
            order_by,
            limit,
        )
        if not filters:
            filters = {}
        return self.__db.get_rows(
            self.__table,
            filters=filters | {"userref": self.__userref},
            exclude=exclude,
            order_by=order_by,
            limit=limit,
        )

    def remove(self: Self, filters: dict) -> None:
        """Remove orders from the orderbook."""
        LOG.debug("Removing orders from the orderbook: %s", filters)
        if not filters:
            raise ValueError("Filters required for removal in orderbook")
        self.__db.delete_row(
            self.__table,
            filters=filters | {"userref": self.__userref},
        )

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
                "symbol": updates.pair,
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
        LOG.debug(
            "Counting orders in the orderbook with filters: %s and exclude: %s",
            filters,
            exclude,
        )
        if not filters:
            filters = {}
        filters |= {"userref": self.__userref}

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
        self.__table = Table(
            "configuration",
            self.__db.metadata,
            Column("id", Integer, primary_key=True),
            Column("userref", Integer, nullable=False),
            Column(
                "version",  # FIXME: This never gets updated
                String,
                nullable=False,
                default=version("infinity-grid"),
            ),
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
            Column("last_price_time", DateTime, nullable=False),
            Column("last_status_update", DateTime, nullable=False),
            extend_existing=True,
        )

        # Create if not exist
        self.__table.create(bind=self.__db.engine, checkfirst=True)

        # Add initial values
        if not self.__db.get_rows(
            self.__table,
            filters={"userref": self.__userref},
        ).fetchone():  # type: ignore[no-untyped-call]
            self.__db.add_row(
                self.__table,
                userref=self.__userref,
                last_price_time=datetime.now(),
                last_status_update=datetime.now(),
            )

    def get(self: Self, filters: dict | None = None) -> dict:
        """Get configuration from the table."""
        LOG.debug(
            "Getting configuration from the table 'configuration' with filter: %s",
            filters,
        )
        if not filters:
            filters = {}

        if result := self.__db.get_rows(
            self.__table,
            filters=filters | {"userref": self.__userref},
        ):
            return next(result)
        raise ValueError(f"No configuration found for passed {filters=}!")

    def update(self: Self, updates: dict) -> None:
        """Update configuration in the table."""
        LOG.debug("Updating configuration in the table: %s", updates)
        self.__db.update_row(
            self.__table,
            filters={"userref": self.__userref},
            updates=updates,
        )


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
            " table: %s",
            txid,
        )
        self.__db.delete_row(
            self.__table,
            filters={
                "userref": self.__userref,
                "txid": txid,
            },
        )

    def get(self: Self, filters: dict | None = None) -> MappingResult:
        """Retrieve unsold buy order txids from the table."""
        LOG.debug(
            "Retrieving unsold buy order txids from the"
            " 'unsold_buy_order_txids' table with filters: %s",
            filters,
        )
        if not filters:
            filters = {}
        return self.__db.get_rows(
            self.__table,
            filters=filters | {"userref": self.__userref},
        )

    def count(self: Self, filters: dict | None = None) -> int:
        """Count unsold buy order txids from the table."""
        LOG.debug(
            "Count unsold buy order txids from the table unsold_buy_order_txids"
            " table with filters: %s",
            filters,
        )
        if not filters:
            filters = {}
        filters |= {"userref": self.__userref}

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
        LOG.debug(
            "Getting pending orders from the 'pending_txids' table with filters: %s",
            filters,
        )
        if not filters:
            filters = {}

        return self.__db.get_rows(
            self.__table,
            filters=filters | {"userref": self.__userref},
        )

    def add(self: Self, txid: str) -> None:
        """Add a pending order to the table."""
        LOG.debug(
            "Adding a pending txid to the 'pending_txids' table: %s",
            txid,
        )
        self.__db.add_row(
            self.__table,
            userref=self.__userref,
            txid=txid,
        )

    def remove(self: Self, txid: str) -> None:
        """Remove a pending order from the table."""
        LOG.debug("Removing pending txid from the 'pending_txids' table: %s", txid)
        self.__db.delete_row(
            self.__table,
            filters={"userref": self.__userref, "txid": txid},
        )

    def count(self: Self, filters: dict | None = None) -> int:
        """Count pending orders in the table."""
        LOG.debug(
            "Counting pending txids of the 'pending_txids' table with filters: %s",
            filters,
        )
        if not filters:
            filters = {}
        filters |= {"userref": self.__userref}

        query = (
            select(func.count())  # pylint: disable=not-callable
            .select_from(self.__table)
            .where(
                *(self.__table.c[column] == value for column, value in filters.items()),
            )
        )
        return self.__db.session.execute(query).scalar()  # type: ignore[no-any-return]
