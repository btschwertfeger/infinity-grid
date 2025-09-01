# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Unit tests for the database module."""


from typing import Generator

import pytest

from infinity_grid.infrastructure.database import (
    Configuration,
    Orderbook,
    PendingTXIDs,
    UnsoldBuyOrderTXIDs,
)
from infinity_grid.models.configuration import DBConfigDTO
from infinity_grid.models.exchange import OrderInfoSchema
from infinity_grid.services.database import DBConnect


@pytest.fixture
def db_connect(db_config: DBConfigDTO) -> Generator:
    """
    Fixture to create a DBConnect instance with an in-memory SQLite database.
    """
    conn = DBConnect(db_config)
    yield conn
    conn.close()


@pytest.fixture
def orderbook(db_connect: DBConnect) -> Orderbook:
    """Fixture to create an Orderbook instance for testing."""
    orderbook = Orderbook(userref=123456789, db=db_connect)
    db_connect.init_db()
    return orderbook


@pytest.fixture
def configuration(db_connect: DBConnect) -> Configuration:
    """Fixture to create a Configuration instance for testing."""
    configuration = Configuration(userref=123456789, db=db_connect)
    db_connect.init_db()
    return configuration


@pytest.fixture
def unsold_buy_order_txids(db_connect: DBConnect) -> UnsoldBuyOrderTXIDs:
    """Fixture to create an UnsoldBuyOrderTXIDs instance for testing."""
    unsold_buy_order_txids = UnsoldBuyOrderTXIDs(userref=123456789, db=db_connect)
    db_connect.init_db()
    return unsold_buy_order_txids


@pytest.fixture
def pending_txids(db_connect: DBConnect) -> PendingTXIDs:
    """Fixture to create a PendingIXIDs instance for testing."""
    pending_txids = PendingTXIDs(userref=123456789, db=db_connect)
    db_connect.init_db()
    return pending_txids


# ==============================================================================


def test_db_connect_init(db_connect: DBConnect) -> None:
    """Test the initialization of DBConnect."""
    assert db_connect.engine is not None
    assert db_connect.session is not None
    assert db_connect.metadata is not None


class TestOrderbook:

    def test_orderbook_add(self, orderbook: Orderbook) -> None:
        """Test adding an order to the orderbook."""
        order = OrderInfoSchema(
            status="open",
            vol_exec=0.0,
            userref=123456789,
            vol=0.1,
            pair="BTC/USD",
            txid="txid1",
            price=50000.0,
            side="buy",
        )
        orderbook.add(order)
        result = orderbook.get_orders(filters={"txid": "txid1"})
        assert result.fetchone() is not None

    def test_orderbook_get_orders(self, orderbook: Orderbook) -> None:
        """Test getting orders from the orderbook."""
        order = OrderInfoSchema(
            status="open",
            vol_exec=0.0,
            userref=123456789,
            vol=0.1,
            pair="BTC/USD",
            txid="txid1",
            price=50000.0,
            side="buy",
        )
        orderbook.add(order)
        result = orderbook.get_orders(filters={"txid": "txid1"})
        assert result.fetchone() is not None

        # Ensure filtering, ordering, and limiting work as expected
        orderbook.add(
            OrderInfoSchema(
                status="open",
                vol_exec=0.0,
                userref=123456789,
                vol=0.1,
                pair="BTC/USD",
                txid="txid2",
                price=51000.0,
                side="buy",
            ),
        )
        orderbook.add(
            OrderInfoSchema(
                status="open",
                vol_exec=0.0,
                userref=123456789,
                vol=0.1,
                pair="BTC/USD",
                txid="txid3",
                price=51000.0,
                side="sell",
            ),
        )

        result = orderbook.get_orders(
            filters={"side": "buy"},
            order_by=("price", "desc"),
            limit=1,
        ).all()
        assert len(result) == 1
        assert result[0]["price"] == 51000
        assert result[0]["txid"] == "txid2"

        result = orderbook.get_orders(
            filters={"side": "buy"},
            order_by=("price", "asc"),
            limit=1,
        ).all()
        assert len(result) == 1
        assert result[0]["price"] == 50000
        assert result[0]["txid"] == "txid1"

        result = orderbook.get_orders(
            filters={"side": "buy"},
            order_by=("price", "asc"),
            limit=2,
        ).all()
        assert len(result) == 2

    def test_orderbook_remove(self, orderbook: Orderbook) -> None:
        """Test removing orders from the orderbook."""
        order = OrderInfoSchema(
            status="open",
            vol_exec=0.0,
            userref=123456789,
            vol=0.1,
            pair="BTC/USD",
            txid="txid1",
            price=50000.0,
            side="buy",
        )
        orderbook.add(order)
        orderbook.remove(filters={"txid": "txid1"})
        result = orderbook.get_orders(filters={"txid": "txid1"})
        assert result.fetchone() is None

    def test_orderbook_update(self, orderbook: Orderbook) -> None:
        """Test updating orders in the orderbook."""
        order = OrderInfoSchema(
            status="open",
            vol_exec=0.0,
            userref=123456789,
            vol=0.1,
            pair="BTC/USD",
            txid="txid1",
            price=50000.0,
            side="buy",
        )
        orderbook.add(order)
        updates = OrderInfoSchema(
            status="open",
            vol_exec=0.0,
            userref=123456789,
            vol=0.2,
            pair="BTC/USD",
            txid="txid1",
            price=51000.0,
            side="buy",
        )
        orderbook.update(updates)
        result = orderbook.get_orders(filters={"txid": "txid1"})
        updated_order = result.fetchone()
        assert updated_order is not None
        assert updated_order["side"] == "buy"
        assert updated_order["price"] == 51000.0
        assert updated_order["volume"] == 0.2

    def test_orderbook_count(self, orderbook: Orderbook) -> None:
        """Test counting orders in the orderbook."""
        order1 = OrderInfoSchema(
            status="open",
            vol_exec=0.0,
            userref=123456789,
            vol=0.1,
            pair="BTC/USD",
            txid="txid1",
            price=50000.0,
            side="buy",
        )
        order2 = OrderInfoSchema(
            status="open",
            vol_exec=0.0,
            userref=123456789,
            vol=0.1,
            pair="BTC/USD",
            txid="txid2",
            price=50000.0,
            side="buy",
        )
        orderbook.add(order1)
        count = orderbook.count()
        assert count == 1
        orderbook.add(order2)
        count = orderbook.count()
        assert count == 2
        count = orderbook.count(filters={"txid": "txid1"})
        assert count == 1
        count = orderbook.count(
            filters={"txid": "txid1"},
            exclude={"symbol": order1.pair},
        )
        assert count == 0
        count = orderbook.count(filters={"symbol": order1.pair})
        assert count == 2


class TestConfiguration:
    def test_configuration_get(self, configuration: Configuration) -> None:
        """Test getting configuration from the table."""
        result = configuration.get()
        assert result["price_of_highest_buy"] == 0.0

    def test_configuration_update(self, configuration: Configuration) -> None:
        """Test updating configuration in the table."""
        updates = {"amount_per_grid": 10}
        configuration.update(updates)
        result = configuration.get(filters={"amount_per_grid": 10})
        assert result["amount_per_grid"] == 10


class TestUnsoldBuyOrderTXIDs:

    def test_unsold_buy_order_txids_add(
        self,
        unsold_buy_order_txids: UnsoldBuyOrderTXIDs,
    ) -> None:
        """Test adding an unsold buy order txid to the table."""
        unsold_buy_order_txids.add(txid="txid1", price=50000.0)
        result = unsold_buy_order_txids.get(filters={"txid": "txid1"})
        assert result.fetchone()["txid"] == "txid1"

    def test_unsold_buy_order_txids_remove(
        self,
        unsold_buy_order_txids: UnsoldBuyOrderTXIDs,
    ) -> None:
        """Test removing an unsold buy order txid from the table."""
        unsold_buy_order_txids.add(txid="txid1", price=50000.0)
        unsold_buy_order_txids.remove(txid="txid1")
        result = unsold_buy_order_txids.get(filters={"txid": "txid1"})
        assert result.fetchone() is None

    def test_unsold_buy_order_txids_get(
        self,
        unsold_buy_order_txids: UnsoldBuyOrderTXIDs,
    ) -> None:
        """Test getting unsold buy order txids from the table."""
        unsold_buy_order_txids.add(txid="txid1", price=50000.0)
        result = unsold_buy_order_txids.get(filters={"txid": "txid1"})
        assert result.fetchone()["txid"] == "txid1"

    def test_unsold_buy_order_txids_count(
        self,
        unsold_buy_order_txids: UnsoldBuyOrderTXIDs,
    ) -> None:
        """Test counting unsold buy order txids from the table."""
        unsold_buy_order_txids.add(txid="txid1", price=50000.0)

        count = unsold_buy_order_txids.count()
        assert count == 1

        unsold_buy_order_txids.add(txid="txid2", price=50000.0)
        count = unsold_buy_order_txids.count()
        assert count == 2

        count = unsold_buy_order_txids.count(filters={"txid": "txid1"})
        assert count == 1


class TestPendingTXIDs:

    def test_pending_txids_add(
        self,
        pending_txids: PendingTXIDs,
    ) -> None:
        """Test adding a pending txid to the table."""
        pending_txids.add(txid="txid1")
        result = pending_txids.get(filters={"txid": "txid1"})
        assert result.fetchone()["txid"] == "txid1"

    def test_pending_txids_remove(
        self,
        pending_txids: PendingTXIDs,
    ) -> None:
        """Test removing a pending txid from the table."""
        pending_txids.add(txid="txid1")
        pending_txids.remove(txid="txid1")
        result = pending_txids.get(filters={"txid": "txid1"})
        assert result.fetchone() is None

    def test_pending_txids_get(self, pending_txids: PendingTXIDs) -> None:
        """Test getting pending txids from the table."""
        pending_txids.add(txid="txid1")
        result = pending_txids.get(filters={"txid": "txid1"})
        assert result.fetchone()["txid"] == "txid1"

    def test_pending_txids_count(self, pending_txids: PendingTXIDs) -> None:
        """Test counting pending txids from the table."""
        pending_txids.add(txid="txid1")
        count = pending_txids.count()
        assert count == 1

        pending_txids.add(txid="txid2")
        count = pending_txids.count()
        assert count == 2

        count = pending_txids.count(filters={"txid": "txid1"})
        assert count == 1
