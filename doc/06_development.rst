.. -*- mode: rst; coding: utf-8 -*-
..
.. Copyright (C) 2025 Benjamin Thomas Schwertfeger
.. All rights reserved.
.. https://github.com/btschwertfeger
..

.. _developer-documentation-section:

Developer Documentation
=======================

The infinity-grid provides interfaces that can be used to add further exchanges
to run the implemented trading strategies on.

State Machine and Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The infinity-grid uses a state machine that must be used for transitioning to
states. It allows the algorithm to determine the current state and perform
actions on that, e.g. not placing orders during the initialization or when being
in an error state.

When developing on the infinity-grid, the transition to the desired state can be
achieved as demonstrated below. Additionally, the ``BotStateError`` must be
raised in order to exit the current context.

.. code-block:: python
    :caption: Use of the state machine during error handling

    try:
        ...
    except Exception as exc:
        self.__state_machine.transition_to(States.ERROR)
        raise BotStateError("Ooops!") from exc

.. autoclass:: infinity_grid.core.state_machine.States
   :members:
   :show-inheritance:
   :inherited-members:

Exchange Interfaces
~~~~~~~~~~~~~~~~~~~

Exchange adapters must implement all functions of the listed interfaces in order
to work properly. Please also read the docstrings of required functions
carefully to avoid errors and misbehavior.

.. autoclass:: infinity_grid.interfaces.exchange.IExchangeRESTService
   :members:
   :show-inheritance:
   :inherited-members:

.. autoclass:: infinity_grid.interfaces.exchange.IExchangeWebSocketService
   :members:
   :show-inheritance:
   :inherited-members:

Exceptions
~~~~~~~~~~

.. automodule:: infinity_grid.exceptions
    :members:

Models and Schemas
~~~~~~~~~~~~~~~~~~

.. automodule:: infinity_grid.models.exchange
    :members:
