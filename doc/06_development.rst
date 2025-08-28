.. -*- mode: rst; coding: utf-8 -*-
..
.. Copyright (C) 2025 Benjamin Thomas Schwertfeger
.. All rights reserved.
.. https://github.com/btschwertfeger
..

.. _developer-documentation-section:

Developer Documentation
=======================

This documentation is intended for developers who want to extend the
infinity-grid trading bot with new exchanges, strategies, or other
functionality. It provides guidance on the architecture, interfaces, and best
practices for contributing to the project.

Architecture Overview
~~~~~~~~~~~~~~~~~~~~~

The infinity-grid trading bot follows a modular architecture with clear
separation of concerns:

1. **Core Components**: State machine, engine, event bus, and other foundational
   elements.
2. **Interfaces**: Well-defined contracts for exchange operations,
   notifications, etc.
3. **Models**: Data structures representing configurations, orders, balances,
   etc.
4. **Adapters**: Implementations of interfaces for specific exchanges or
   services.
5. **Strategies**: Trading algorithms that use the adapters to execute trades.
6. **Services**: Supporting functionality like database access and
   notifications.
7. **Infrastructure**: Low-level components like database management.

Project Structure
~~~~~~~~~~~~~~~~~

.. code-block:: text
    :caption: Schematic Project Structure

    infinity_grid/
    ├── exceptions.py
    ├── adapters/              # Implementations of interfaces
    │   ├── exchanges/         # Exchange-specific adapters
    │   │   └── kraken.py      # Kraken exchange adapter
    │   └── notification.py    # Notification service adapters
    ├── core/                  # Core functionality
    │   ├── cli.py             # Command-line interface
    │   ├── engine.py          # The main engine driving the algorithm
    │   ├── event_bus.py       # Event management
    │   └── state_machine.py   # Bot state management
    ├── infrastructure/        # Low-level components
    │   └── database.py        # Database schemas and access
    ├── interfaces/            # Interface definitions
    │   ├── exchange.py        # Exchange interface
    │   └── notification.py    # Notification interface
    ├── models/                # Data models
    │   ├── configuration.py   # Configuration models
    │   └── exchange.py        # Exchange-related models
    ├── services/              # Supporting services
    │   ├── database.py        # Database service
    │   └── notification.py    # Notification service
    └── strategies/            # Trading strategies
        ├── grid_base.py       # Base grid strategy
        ├── grid_hodl.py       # HODL grid strategy
        ├── grid_sell.py       # Sell grid strategy
        ├── c_dca.py           # Dollar-cost averaging strategy
        └── swing.py           # Swing trading strategy

Extension Points
~~~~~~~~~~~~~~~~

The infinity-grid bot is designed to be extended in several ways:

1. **Adding New Exchanges**: Implement the exchange interfaces to support
   additional trading platforms.
2. **Creating New Strategies**: Extend the base strategy classes to implement
   new trading algorithms.
3. **Custom Notifications**: Extend the notification adapters for different
   notification channels.
4. **Enhanced Monitoring**: Add new metrics or monitoring capabilities.

Adding a New Exchange Adapter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To add support for a new exchange, you need to create an adapter that implements
both the REST and WebSocket interfaces:

1. **Create a new file** in ``infinity_grid/adapters/exchanges/`` named after
   the exchange (e.g., ``binance.py``)
2. **Implement the REST interface** by creating a class that inherits from
   :py:class:`infinity_grid.interfaces.exchange.IExchangeRESTService`
3. **Implement the WebSocket interface** by creating a class that inherits from
   :py:class:`infinity_grid.interfaces.exchange.IExchangeWebSocketService`
4. **Define the exchange domain** by creating an instance of
   :py:class:`infinity_grid.models.exchange.ExchangeDomain` with the exchange's
   specific naming conventions
5. **Adapt to exchange-specific behavior** by ensuring that the implemented
   interfaces behave as expected. Feel free to orientate on existing adapters.

.. code-block:: python
    :caption: Sample structure for a new exchange adapter

    from infinity_grid.interfaces.exchange import IExchangeRESTService, IExchangeWebSocketService
    from infinity_grid.models.exchange import ExchangeDomain

    # Define exchange-specific constants
    NEW_EXCHANGE_DOMAIN = ExchangeDomain(
        EXCHANGE="NewExchange",
        BUY="buy",
        SELL="sell",
        OPEN="open",
        CLOSED="closed",
        CANCELED="canceled",
        EXPIRED="expired",
        PENDING="pending",
    )

    class NewExchangeRESTService(IExchangeRESTService):
        """Implementation of the REST interface for NewExchange"""

        def __init__(self, api_public_key, api_secret_key, state_machine, base_currency, quote_currency):
            # Initialize the REST client
            # Set up any exchange-specific configuration

        def check_api_key_permissions(self):
            # Implement permission checking logic

        # Implement all other required methods from IExchangeRESTService

    class NewExchangeWebSocketService(IExchangeWebSocketService):
        """Implementation of the WebSocket interface for NewExchange"""

        def __init__(self, api_public_key, api_secret_key, state_machine, event_bus):
            # Initialize the WebSocket client
            # Set up event handlers

        # Implement all required methods from IExchangeWebSocketService

Creating a New Trading Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a new trading strategy, you should extend one of the existing base
strategies or create a completely new one:

1. **Create a new file** in ``infinity_grid/strategies/`` named after your
   strategy (e.g., ``my_strategy.py``)
2. **Extend an appropriate base class** such as
   :py:class:`infinity_grid.strategies.grid_base.GridStrategyBase` for
   grid-based strategies
3. **Implement the required methods** based on your trading logic
4. **Use the state machine** to manage the strategy's state transitions
5. **Handle events** using the event bus for asynchronous operations

.. code-block:: python
    :caption: Sample structure for a completely new trading strategy

    from infinity_grid.strategies.grid_base import GridStrategyBase
    from infinity_grid.core.state_machine import States
    from infinity_grid.exceptions import BotStateError

    class MyCustomStrategy(GridStrategyBase):
        """This is a new sample strategy, based on the GridStrategyBase

        NOTE: When deviating from grid-like trading, make sure to mock, disable,
              or overwrite all functions of the GridStrategyBase.
        """

        async def run(self):
            """Main entry point for the strategy"""
            try:
                # Initialize strategy-specific components
                await self._initialize()

                # Start trading
                await self._start_trading()

            except Exception as exc:
                self._state_machine.transition_to(States.ERROR)
                raise BotStateError("Strategy initialization failed") from exc

        async def _initialize(self):
            """Initialize strategy-specific components"""
            # Implement initialization logic

        async def _start_trading(self):
            """Start the trading process"""
            # Implement trading logic

        # Implement other strategy-specific methods

Testing Your Extensions
~~~~~~~~~~~~~~~~~~~~~~~

When developing new adapters or strategies, it's important to test them
thoroughly:

1. **Unit Tests**: Create unit tests in the ``tests/unit/`` directory to test
   your implementations.
2. **Integration Tests**: Add integration tests in ``tests/integration/`` for
   end-to-end testing.
3. **Mocking**: Use mocking to simulate exchange responses without making actual
   API calls.

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

Strategies
~~~~~~~~~~

.. automodule:: infinity_grid.strategies.grid_base
    :members:
    :private-members:

.. automodule:: infinity_grid.strategies.c_dca
    :members:
    :private-members:

.. automodule:: infinity_grid.strategies.grid_hodl
    :members:
    :private-members:

.. automodule:: infinity_grid.strategies.grid_sell
    :members:
    :private-members:

.. automodule:: infinity_grid.strategies.swing
    :members:
    :private-members:
