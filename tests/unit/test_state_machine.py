# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Unit tests for the StateMachine class."""

import asyncio
from typing import Callable
from unittest.mock import Mock

import pytest

from infinity_grid.core.state_machine import StateMachine, States


@pytest.fixture
def state_machine() -> StateMachine:
    """Create a fresh StateMachine instance for each test"""
    return StateMachine()


class TestStateMachineBasic:
    def test_initialization_default(self, state_machine: StateMachine) -> None:
        """Test default initialization"""
        assert state_machine.state == States.INITIALIZING

    def test_initialization_custom(self) -> None:
        """Test custom initialization with specific state"""
        sm = StateMachine(initial_state=States.RUNNING)
        assert sm.state == States.RUNNING

    def test_invalid_transition_shutdown_to_running(self) -> None:
        """Test invalid transition from SHUTDOWN_REQUESTED to RUNNING"""
        sm = StateMachine(initial_state=States.SHUTDOWN_REQUESTED)
        with pytest.raises(ValueError, match=r"Invalid state transition.*"):
            sm.transition_to(States.RUNNING)

    def test_register_and_execute_callback(self, state_machine: StateMachine) -> None:
        """Test registering and executing a callback"""
        mock_callback = Mock()
        state_machine.register_callback(States.RUNNING, mock_callback)

        # Before transition - callback shouldn't be called
        mock_callback.assert_not_called()

        # After transition - callback should be called once
        state_machine.transition_to(States.RUNNING)
        mock_callback.assert_called_once()

    def test_multiple_callbacks_for_state(self, state_machine: StateMachine) -> None:
        """Test registering and executing multiple callbacks for the same state"""
        callback1 = Mock()
        callback2 = Mock()

        state_machine.register_callback(States.RUNNING, callback1)
        state_machine.register_callback(States.RUNNING, callback2)

        state_machine.transition_to(States.RUNNING)

        callback1.assert_called_once()
        callback2.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_for_shutdown_when_already_in_shutdown_state(self) -> None:
        """Test wait_for_shutdown when already in SHUTDOWN_REQUESTED state"""
        sm = StateMachine(initial_state=States.SHUTDOWN_REQUESTED)

        # Should return immediately since already in shutdown state
        await sm.wait_for_shutdown()
        assert sm.state == States.SHUTDOWN_REQUESTED

    @pytest.mark.asyncio
    async def test_wait_for_shutdown_when_already_in_error_state(self) -> None:
        """Test wait_for_shutdown when already in ERROR state"""
        sm = StateMachine(initial_state=States.ERROR)

        # Should return immediately since already in error state
        await sm.wait_for_shutdown()
        assert sm.state == States.ERROR

    @pytest.mark.asyncio
    async def test_wait_for_shutdown_transition_to_shutdown_requested(self) -> None:
        """Test wait_for_shutdown waits for transition to SHUTDOWN_REQUESTED"""
        sm = StateMachine(initial_state=States.RUNNING)

        async def trigger_shutdown() -> None:
            # Small delay to simulate async work
            await asyncio.sleep(0.01)
            sm.transition_to(States.SHUTDOWN_REQUESTED)

        # Start both tasks
        wait_task = asyncio.create_task(sm.wait_for_shutdown())
        trigger_task = asyncio.create_task(trigger_shutdown())

        # Wait for both to complete
        await asyncio.gather(wait_task, trigger_task)

        assert sm.state == States.SHUTDOWN_REQUESTED

    @pytest.mark.asyncio
    async def test_wait_for_shutdown_transition_to_error(self) -> None:
        """Test wait_for_shutdown waits for transition to ERROR"""
        sm = StateMachine(initial_state=States.RUNNING)

        async def trigger_error() -> None:
            await asyncio.sleep(0.01)
            sm.transition_to(States.ERROR)

        wait_task = asyncio.create_task(sm.wait_for_shutdown())
        trigger_task = asyncio.create_task(trigger_error())

        await asyncio.gather(wait_task, trigger_task)

        assert sm.state == States.ERROR

    @pytest.mark.asyncio
    async def test_wait_for_shutdown_multiple_calls(self) -> None:
        """Test multiple calls to wait_for_shutdown work correctly"""
        sm = StateMachine(initial_state=States.RUNNING)

        # Multiple wait calls should all complete when shutdown occurs
        wait_task1 = asyncio.create_task(sm.wait_for_shutdown())
        wait_task2 = asyncio.create_task(sm.wait_for_shutdown())
        wait_task3 = asyncio.create_task(sm.wait_for_shutdown())

        async def trigger_shutdown() -> None:
            await asyncio.sleep(0.01)
            sm.transition_to(States.SHUTDOWN_REQUESTED)

        trigger_task = asyncio.create_task(trigger_shutdown())

        # All should complete
        await asyncio.gather(wait_task1, wait_task2, wait_task3, trigger_task)

        assert sm.state == States.SHUTDOWN_REQUESTED

    @pytest.mark.asyncio
    async def test_wait_for_shutdown_event_creation(self) -> None:
        """Test that wait_for_shutdown creates shutdown event only once"""
        sm = StateMachine(initial_state=States.RUNNING)

        # First call should create the event
        assert not hasattr(sm, "_shutdown_event")

        # Start wait_for_shutdown (but don't await yet)
        wait_task = asyncio.create_task(sm.wait_for_shutdown())
        await asyncio.sleep(0.001)  # Let it start

        # Now the event should exist
        assert hasattr(sm, "_shutdown_event")
        first_event = sm._shutdown_event

        # Second call should reuse the same event
        wait_task2 = asyncio.create_task(sm.wait_for_shutdown())
        await asyncio.sleep(0.001)

        assert sm._shutdown_event is first_event

        # Trigger shutdown to clean up
        sm.transition_to(States.SHUTDOWN_REQUESTED)
        await asyncio.gather(wait_task, wait_task2)

    def test_state_property_immutability(self, state_machine: StateMachine) -> None:
        """Test that state property is read-only and returns current state"""
        assert state_machine.state == States.INITIALIZING

        # State should not be directly settable (no setter defined)
        with pytest.raises(AttributeError):
            state_machine.state = States.RUNNING  # type: ignore[misc]

        # State should only change through transition_to
        state_machine.transition_to(States.RUNNING)
        assert state_machine.state == States.RUNNING


class TestStateMachineStateTransitions:

    def test_valid_state_transitions(self, state_machine: StateMachine) -> None:
        """Test valid state transitions"""
        # INITIALIZING -> RUNNING
        state_machine.transition_to(States.RUNNING)
        assert state_machine.state == States.RUNNING

        # RUNNING -> ERROR
        state_machine.transition_to(States.ERROR)
        assert state_machine.state == States.ERROR

        # ERROR -> RUNNING (recovery)
        state_machine.transition_to(States.RUNNING)
        assert state_machine.state == States.RUNNING

        # RUNNING -> SHUTDOWN_REQUESTED
        state_machine.transition_to(States.SHUTDOWN_REQUESTED)
        assert state_machine.state == States.SHUTDOWN_REQUESTED

    def test_invalid_transition_initializing_to_invalid_state(
        self,
        state_machine: StateMachine,
    ) -> None:
        """Test transition to non-existent state"""
        with pytest.raises(ValueError, match=r"Invalid state transition from.*"):
            state_machine.transition_to("INVALID_STATE")  # type: ignore[arg-type]

    def test_same_state_transition(self, state_machine: StateMachine) -> None:
        """Test transition to the same state (should be no-op)"""
        state_machine.transition_to(States.RUNNING)
        # Transitioning to the same state should not raise an error
        state_machine.transition_to(States.RUNNING)
        assert state_machine.state == States.RUNNING

    def test_callbacks_for_different_states(self, state_machine: StateMachine) -> None:
        """Test callbacks for different states are called appropriately"""
        running_cb = Mock()
        error_cb = Mock()

        state_machine.register_callback(States.RUNNING, running_cb)
        state_machine.register_callback(States.ERROR, error_cb)

        state_machine.transition_to(States.RUNNING)
        running_cb.assert_called_once()
        error_cb.assert_not_called()

        running_cb.reset_mock()

        state_machine.transition_to(States.ERROR)
        running_cb.assert_not_called()
        error_cb.assert_called_once()

    def test_fact_persistence_across_transitions(
        self,
        state_machine: StateMachine,
    ) -> None:
        """Test that facts are persistent across state transitions"""
        # Set initial facts
        state_machine.facts = {"ready_to_trade": True}

        # Transition states
        state_machine.transition_to(States.RUNNING)
        assert state_machine.facts["ready_to_trade"] is True

        state_machine.transition_to(States.ERROR)
        assert state_machine.facts["ready_to_trade"] is True

        state_machine.transition_to(States.SHUTDOWN_REQUESTED)
        assert state_machine.facts["ready_to_trade"] is True

    def test_facts_property_getter(self, state_machine: StateMachine) -> None:
        """Test facts property getter returns correct data"""
        initial_facts = state_machine.facts
        assert isinstance(initial_facts, dict)
        assert len(initial_facts) == 0

        # Add some facts
        state_machine.facts = {"trading_enabled": True, "connection_established": False}
        facts = state_machine.facts
        assert facts["trading_enabled"] is True
        assert facts["connection_established"] is False

    def test_facts_property_setter_updates_existing_facts(
        self,
        state_machine: StateMachine,
    ) -> None:
        """Test facts setter updates existing facts correctly"""
        # Set initial facts
        state_machine.facts = {"api_connected": True, "balance_sufficient": False}

        # Update some facts
        state_machine.facts = {"api_connected": False, "new_fact": True}

        facts = state_machine.facts
        assert facts["api_connected"] is False  # Updated
        assert facts["balance_sufficient"] is False  # Preserved
        assert facts["new_fact"] is True  # Added

    def test_facts_property_setter_with_empty_dict(
        self,
        state_machine: StateMachine,
    ) -> None:
        """Test facts setter with empty dictionary"""
        # Set some initial facts
        state_machine.facts = {"initial": True}

        # Set empty facts (should not clear existing facts)
        state_machine.facts = {}

        # Original facts should still be there
        assert state_machine.facts["initial"] is True

    def test_transition_error_to_error_allowed(
        self,
        state_machine: StateMachine,
    ) -> None:
        """Test that ERROR to ERROR transition is allowed (self-transition)"""
        state_machine.transition_to(States.ERROR)
        assert state_machine.state == States.ERROR

        # Should allow ERROR -> ERROR transition
        state_machine.transition_to(States.ERROR)
        assert state_machine.state == States.ERROR

    def test_all_valid_transitions_from_initializing(
        self,
        state_machine: StateMachine,
    ) -> None:
        """Test all valid transitions from INITIALIZING state"""
        # INITIALIZING -> RUNNING
        state_machine.transition_to(States.RUNNING)
        assert state_machine.state == States.RUNNING

        # Reset to INITIALIZING for next test
        sm2 = StateMachine()
        sm2.transition_to(States.SHUTDOWN_REQUESTED)
        assert sm2.state == States.SHUTDOWN_REQUESTED

        # Reset to INITIALIZING for next test
        sm3 = StateMachine()
        sm3.transition_to(States.ERROR)
        assert sm3.state == States.ERROR

    def test_all_valid_transitions_from_running(self) -> None:
        """Test all valid transitions from RUNNING state"""
        sm = StateMachine(initial_state=States.RUNNING)

        # RUNNING -> ERROR
        sm.transition_to(States.ERROR)
        assert sm.state == States.ERROR

        # Reset to RUNNING for next test
        sm2 = StateMachine(initial_state=States.RUNNING)
        sm2.transition_to(States.SHUTDOWN_REQUESTED)
        assert sm2.state == States.SHUTDOWN_REQUESTED

    def test_all_valid_transitions_from_error(self) -> None:
        """Test all valid transitions from ERROR state"""
        sm = StateMachine(initial_state=States.ERROR)

        # ERROR -> RUNNING (recovery)
        sm.transition_to(States.RUNNING)
        assert sm.state == States.RUNNING

        # Reset to ERROR for next test
        sm2 = StateMachine(initial_state=States.ERROR)
        sm2.transition_to(States.SHUTDOWN_REQUESTED)
        assert sm2.state == States.SHUTDOWN_REQUESTED

        # Reset to ERROR for self-transition test
        sm3 = StateMachine(initial_state=States.ERROR)
        sm3.transition_to(States.ERROR)
        assert sm3.state == States.ERROR

    def test_no_valid_transitions_from_shutdown_requested(self) -> None:
        """Test that no transitions are allowed from SHUTDOWN_REQUESTED state"""
        sm = StateMachine(initial_state=States.SHUTDOWN_REQUESTED)

        # All transitions from SHUTDOWN_REQUESTED should fail
        with pytest.raises(ValueError, match=r"Invalid state transition.*"):
            sm.transition_to(States.RUNNING)

        with pytest.raises(ValueError, match=r"Invalid state transition.*"):
            sm.transition_to(States.ERROR)

        with pytest.raises(ValueError, match=r"Invalid state transition.*"):
            sm.transition_to(States.INITIALIZING)

    def test_callback_exception_handling(self, state_machine: StateMachine) -> None:
        """Test that callback exceptions don't break state transitions"""

        def failing_callback() -> None:
            raise RuntimeError("Callback failed")

        def working_callback() -> None:
            working_callback.called = True  # type: ignore[attr-defined]

        working_callback.called = False  # type: ignore[attr-defined]

        state_machine.register_callback(States.RUNNING, failing_callback)
        state_machine.register_callback(States.RUNNING, working_callback)

        # Transition should succeed despite callback exception
        with pytest.raises(RuntimeError, match="Callback failed"):
            state_machine.transition_to(States.RUNNING)

        # State should have changed despite the exception
        assert state_machine.state == States.RUNNING
        # The second callback should not have been called due to the exception
        assert working_callback.called is False  # type: ignore[attr-defined]

    def test_callback_execution_order(self, state_machine: StateMachine) -> None:
        """Test that callbacks are executed in registration order"""
        execution_order = []

        def callback1() -> None:
            execution_order.append(1)

        def callback2() -> None:
            execution_order.append(2)

        def callback3() -> None:
            execution_order.append(3)

        state_machine.register_callback(States.RUNNING, callback1)
        state_machine.register_callback(States.RUNNING, callback2)
        state_machine.register_callback(States.RUNNING, callback3)

        state_machine.transition_to(States.RUNNING)

        assert execution_order == [1, 2, 3]

    def test_define_transitions_returns_correct_structure(
        self,
        state_machine: StateMachine,
    ) -> None:
        """Test that _define_transitions returns the expected transition rules"""
        transitions = state_machine._define_transitions()

        # Check structure and content
        assert isinstance(transitions, dict)
        assert len(transitions) == 4

        # Check INITIALIZING transitions
        assert States.INITIALIZING in transitions
        assert set(transitions[States.INITIALIZING]) == {
            States.RUNNING,
            States.SHUTDOWN_REQUESTED,
            States.ERROR,
        }

        # Check RUNNING transitions
        assert States.RUNNING in transitions
        assert set(transitions[States.RUNNING]) == {
            States.ERROR,
            States.SHUTDOWN_REQUESTED,
        }

        # Check ERROR transitions
        assert States.ERROR in transitions
        assert set(transitions[States.ERROR]) == {
            States.RUNNING,
            States.SHUTDOWN_REQUESTED,
            States.ERROR,
        }

        # Check SHUTDOWN_REQUESTED transitions (empty)
        assert States.SHUTDOWN_REQUESTED in transitions
        assert transitions[States.SHUTDOWN_REQUESTED] == []

    def test_multiple_state_transitions_complex_workflow(
        self,
        state_machine: StateMachine,
    ) -> None:
        """Test a complex workflow with multiple state transitions"""
        callback_history = []

        def track_transition(state_name: str) -> Callable[[], None]:
            def callback() -> None:
                callback_history.append(state_name)

            return callback

        # Register callbacks for all states
        state_machine.register_callback(States.RUNNING, track_transition("RUNNING"))
        state_machine.register_callback(States.ERROR, track_transition("ERROR"))
        state_machine.register_callback(
            States.SHUTDOWN_REQUESTED,
            track_transition("SHUTDOWN"),
        )

        # Complex workflow: INITIALIZING -> RUNNING -> ERROR -> RUNNING -> SHUTDOWN_REQUESTED
        assert state_machine.state == States.INITIALIZING

        state_machine.transition_to(States.RUNNING)
        assert state_machine.state == States.RUNNING

        state_machine.transition_to(States.ERROR)
        assert state_machine.state == States.ERROR

        state_machine.transition_to(States.RUNNING)  # Recovery
        assert state_machine.state == States.RUNNING

        state_machine.transition_to(States.SHUTDOWN_REQUESTED)
        assert state_machine.state == States.SHUTDOWN_REQUESTED

        # Check callback execution history
        assert callback_history == ["RUNNING", "ERROR", "RUNNING", "SHUTDOWN"]
