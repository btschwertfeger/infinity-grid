# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Custom exceptions for the Infinity Grid trading bot."""


class BotStateError(Exception):
    """
    Custom exception for terminating the algorithm due to an error state.

    This exception must only be raised in functions within the running loop,
    that would otherwise continue running or returning something time before the
    algorithm is terminating due to an error state.

    Attributes:
        message (str): The error message to be displayed.

    Example:

    .. code-block:: python

        def func():
            try:
                do_something()
            except Exception as exc:
                message = "Exception while processing message."
                LOG.error(msg=message, exc_info=exc)
                self.state_machine.transition_to(States.ERROR)
                raise GridBotErrorState(message) from exc
    """


class UnknownOrderError(Exception):
    """
    Exception used to be raised when an order that was requested is unknown.
    """
