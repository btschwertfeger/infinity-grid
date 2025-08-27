# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

""" State machine for the Infinity Grid trading bot. """

import asyncio
from enum import Enum, auto
from logging import getLogger
from typing import Callable, Self

LOG = getLogger(__name__)


class States(Enum):
    """Represents the state of the trading bot"""

    INITIALIZING = auto()  #: The algorithm is initializing from the beginning.
    RUNNING = auto()  #: The algorithm is running.
    SHUTDOWN_REQUESTED = auto()  #: A request to shutdown is being processed.
    ERROR = auto()  #: The algorithm encountered an error and is handling it.


class StateMachine:
    """Manages state transitions of the algorithm"""

    def __init__(
        self: Self,
        initial_state: States = States.INITIALIZING,
    ) -> None:
        self._state: States = initial_state
        self._transitions = self._define_transitions()
        self._callbacks: dict[States, list[Callable]] = {}
        self._facts: dict = {}

    def _define_transitions(self: Self) -> dict[States, list[States]]:
        return {
            States.INITIALIZING: [
                States.RUNNING,
                States.SHUTDOWN_REQUESTED,
                States.ERROR,
            ],
            States.RUNNING: [States.ERROR, States.SHUTDOWN_REQUESTED],
            States.ERROR: [States.RUNNING, States.SHUTDOWN_REQUESTED, States.ERROR],
            States.SHUTDOWN_REQUESTED: [],
        }

    def transition_to(self: Self, new_state: States) -> None:
        """Attempt to transition to a new state"""
        LOG.debug("Transitioning from %s to %s", self._state, new_state)
        if new_state == self._state:
            return

        if new_state not in self._transitions[self._state]:
            raise ValueError(
                f"Invalid state transition from {self._state} to {new_state}",
            )

        self._state = new_state

        # Execute callbacks for this transition if any
        if new_state in self._callbacks:
            for callback in self._callbacks[new_state]:
                callback()

    @property
    def state(self: Self) -> States:
        return self._state

    @property
    def facts(self: Self) -> dict[str, bool]:
        """Return the current facts of the state machine"""
        return self._facts

    @facts.setter
    def facts(self: Self, new_facts: dict[str, bool]) -> None:
        """Update the facts of the state machine"""
        for key, value in new_facts.items():
            self._facts[key] = value

    def register_callback(
        self: Self,
        to_state: States,
        callback: Callable,
    ) -> None:
        """Register a callback to be executed on specific state transitions"""
        LOG.debug(
            "Registering callback for state transition to %s: %s",
            to_state,
            callback,
        )
        if to_state not in self._callbacks:
            self._callbacks[to_state] = []
        self._callbacks[to_state].append(callback)

    async def wait_for_shutdown(self: Self) -> None:
        """
        Wait until the state machine transitions to a shutdown state.
        Returns when state becomes SHUTDOWN_REQUESTED or ERROR.
        """
        # Create an event if it doesn't exist yet
        if not hasattr(self, "_shutdown_event"):
            self._shutdown_event = asyncio.Event()

            # Register callbacks to set the event when shutdown states are reached
            def set_shutdown_event() -> None:
                self._shutdown_event.set()

            self.register_callback(States.SHUTDOWN_REQUESTED, set_shutdown_event)
            self.register_callback(States.ERROR, set_shutdown_event)

        # If already in a shutdown state, set the event immediately
        if self.state in {States.SHUTDOWN_REQUESTED, States.ERROR}:
            self._shutdown_event.set()

        # Wait for the shutdown event
        await self._shutdown_event.wait()
