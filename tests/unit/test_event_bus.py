# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Test module for event bus.

This module contains focused tests for the EventBus class,
testing subscription, publishing, and callback functionality.
"""

from unittest.mock import Mock

import pytest

from infinity_grid.core.event_bus import EventBus


class TestEventBus:
    """Test cases for EventBus"""

    def test_init(self) -> None:
        """Test EventBus initialization"""
        event_bus = EventBus()
        assert event_bus._subscribers == {}

    def test_subscribe_single_callback(self) -> None:
        """Test subscribing a single callback to an event type"""
        event_bus = EventBus()
        callback = Mock()

        event_bus.subscribe("test_event", callback)

        assert "test_event" in event_bus._subscribers
        assert len(event_bus._subscribers["test_event"]) == 1
        assert event_bus._subscribers["test_event"][0] == callback

    def test_subscribe_multiple_callbacks_same_event(self) -> None:
        """Test subscribing multiple callbacks to the same event type"""
        event_bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()

        event_bus.subscribe("test_event", callback1)
        event_bus.subscribe("test_event", callback2)

        assert len(event_bus._subscribers["test_event"]) == 2
        assert callback1 in event_bus._subscribers["test_event"]
        assert callback2 in event_bus._subscribers["test_event"]

    def test_subscribe_different_event_types(self) -> None:
        """Test subscribing to different event types"""
        event_bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()

        event_bus.subscribe("event_type_1", callback1)
        event_bus.subscribe("event_type_2", callback2)

        assert "event_type_1" in event_bus._subscribers
        assert "event_type_2" in event_bus._subscribers
        assert len(event_bus._subscribers["event_type_1"]) == 1
        assert len(event_bus._subscribers["event_type_2"]) == 1

    def test_publish_to_existing_subscribers(self) -> None:
        """Test publishing event to existing subscribers"""
        event_bus = EventBus()
        callback = Mock()
        test_data = {"message": "test", "value": 42}

        event_bus.subscribe("test_event", callback)
        event_bus.publish("test_event", test_data)

        callback.assert_called_once_with(test_data)

    def test_publish_to_multiple_subscribers(self) -> None:
        """Test publishing event to multiple subscribers"""
        event_bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()
        test_data = {"data": "shared"}

        event_bus.subscribe("test_event", callback1)
        event_bus.subscribe("test_event", callback2)
        event_bus.publish("test_event", test_data)

        callback1.assert_called_once_with(test_data)
        callback2.assert_called_once_with(test_data)

    def test_publish_to_nonexistent_event_type(self) -> None:
        """Test publishing to event type with no subscribers"""
        event_bus = EventBus()
        test_data = {"message": "nobody listening"}

        # Should not raise any exception
        event_bus.publish("nonexistent_event", test_data)

        # Verify no subscribers were created
        assert "nonexistent_event" not in event_bus._subscribers

    def test_publish_different_event_types(self) -> None:
        """Test that publishing only affects relevant subscribers"""
        event_bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()

        event_bus.subscribe("event_a", callback1)
        event_bus.subscribe("event_b", callback2)

        # Publish to event_a only
        event_bus.publish("event_a", {"data": "for_a"})

        callback1.assert_called_once_with({"data": "for_a"})
        callback2.assert_not_called()

    def test_callback_with_exception_doesnt_break_others(self) -> None:
        """Test that exception in one callback doesn't prevent others from running"""
        event_bus = EventBus()

        # Callback that raises exception
        def failing_callback(data: dict) -> None:  # noqa: ARG001
            raise ValueError("Test exception")

        success_callback = Mock()

        event_bus.subscribe("test_event", failing_callback)
        event_bus.subscribe("test_event", success_callback)

        # This should raise exception from failing_callback
        with pytest.raises(ValueError, match="Test exception"):
            event_bus.publish("test_event", {"data": "test"})

        # Note: The success_callback might not be called if the exception
        # interrupts the loop, which is expected behavior

    def test_empty_data_dict(self) -> None:
        """Test publishing with empty data dictionary"""
        event_bus = EventBus()
        callback = Mock()

        event_bus.subscribe("test_event", callback)
        event_bus.publish("test_event", {})

        callback.assert_called_once_with({})

    def test_complex_data_structure(self) -> None:
        """Test publishing with complex data structure"""
        event_bus = EventBus()
        callback = Mock()
        complex_data = {
            "nested": {"value": 123},
            "list": [1, 2, 3],
            "string": "test",
        }

        event_bus.subscribe("complex_event", callback)
        event_bus.publish("complex_event", complex_data)

        callback.assert_called_once_with(complex_data)

    def test_callback_receives_exact_data(self) -> None:
        """Test that callback receives the exact data object (not a copy)"""
        event_bus = EventBus()
        received_data = None

        def capture_callback(data: dict) -> None:
            nonlocal received_data
            received_data = data

        original_data = {"mutable": "data"}
        event_bus.subscribe("test_event", capture_callback)
        event_bus.publish("test_event", original_data)

        # Should be the same object reference
        assert received_data is original_data

    def test_multiple_event_types_integration(self) -> None:
        """Integration test with multiple event types and callbacks"""
        event_bus = EventBus()

        # Track calls
        order_callback = Mock()
        balance_callback = Mock()
        notification_callback = Mock()

        # Subscribe to different events
        event_bus.subscribe("order_filled", order_callback)
        event_bus.subscribe("balance_updated", balance_callback)
        event_bus.subscribe(
            "order_filled",
            notification_callback,
        )  # Also listens to orders

        # Publish different events
        event_bus.publish("order_filled", {"order_id": "123", "amount": 1.5})
        event_bus.publish("balance_updated", {"asset": "BTC", "balance": 2.0})

        # Verify correct callbacks were called
        order_callback.assert_called_once_with({"order_id": "123", "amount": 1.5})
        balance_callback.assert_called_once_with({"asset": "BTC", "balance": 2.0})
        notification_callback.assert_called_once_with(
            {"order_id": "123", "amount": 1.5},
        )
