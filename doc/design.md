# Design notes

This document contains design decisions and potential future improvement ideas
that need to be explored.

## Improvement Ideas

### Architecture

1. **Monolithic Class**: KrakenInfinityGridBot is a massive god class doing too
   much - websockets, order management, API interaction, database operations,
   and signal handling. This violates SRP and makes testing nearly impossible.

   Idea: Separate the components like:

   ```
   src/infinity_grid/
   ├── core/
   │   ├── bot.py                 # Orchestration only
   │   └── state_machine.py       # Proper state management
   ├── infrastructure/
   │   ├── websocket_client.py    # Handles websocket connections only
   │   ├── rest_client.py         # REST API interactions
   │   ├── database.py            # Data access layer (existing)
   │   └── messaging.py           # Telegram notifications
   ├── domain/
   │   ├── order.py               # Order domain model
   │   ├── market_data.py         # Price ticker and market state
   │   └── strategies/            # Strategy implementations
   │       ├── base_strategy.py   # Strategy interface
   │       ├── grid_hodl.py
   │       ├── grid_sell.py
   │       ├── cdca.py
   │       └── swing.py
   └── application/
       ├── order_service.py       # Order management (extracted logic)
       ├── setup_service.py       # Setup logic (extracted)
       └── config_service.py      # Configuration management
   ```

2. **Tangled State Management**: The code uses multiple Boolean flags (init_done,
   is_ready_to_trade, \_\_ticker_channel_connected, etc.) creating a complex state
   machine that's prone to race conditions.

   Idea: Replace Boolean Flags with a State Machine

   ```python
   from enum import Enum, auto

   class BotState(Enum):
       """Represents the state of the trading bot"""
       INITIALIZING = auto()
       CONNECTING = auto()
       SYNCING_ORDERBOOK = auto()
       READY = auto()
       PROCESSING_WEBSOCKET_EVENT = auto()
       PLACING_ORDER = auto()
       CANCELLING_ORDER = auto()
       SHUTDOWN_REQUESTED = auto()
       SHUTTING_DOWN = auto()
       ERROR = auto()

   class StateMachine:
       """Manages state transitions in the bot"""

       def __init__(self, initial_state=BotState.INITIALIZING):
           self._state = initial_state
           self._transitions = self._define_transitions()
           self._callbacks = {}

       def _define_transitions(self):
           # Define allowed state transitions
           return {
               BotState.INITIALIZING: [BotState.CONNECTING, BotState.ERROR, BotState.SHUTDOWN_REQUESTED],
               BotState.CONNECTING: [BotState.SYNCING_ORDERBOOK, BotState.ERROR, BotState.SHUTDOWN_REQUESTED],
               # etc...
           }

       def transition_to(self, new_state):
           """Attempt to transition to a new state"""
           if new_state not in self._transitions[self._state]:
               raise ValueError(f"Invalid state transition from {self._state} to {new_state}")

           old_state = self._state
           self._state = new_state

           # Execute callbacks for this transition if any
           if (old_state, new_state) in self._callbacks:
               for callback in self._callbacks[(old_state, new_state)]:
                   callback(old_state, new_state)

       @property
       def state(self):
           return self._state

       def register_transition_callback(self, from_state, to_state, callback):
           """Register a callback to be executed on specific state transitions"""
           key = (from_state, to_state)
           if key not in self._callbacks:
               self._callbacks[key] = []
           self._callbacks[key].append(callback)
   ```

3. **Insufficient Separation of Concerns**: Despite having OrderManager and
   SetupManager classes, the main class still does too much and knows too much
   about implementation details.

   Idea: Implement Event-Based Architecture

   ```python
   from typing import Callable, Any
   from dataclasses import dataclass

   @dataclass
   class Event:
       """Base event class"""
       type: str
       data: dict[str, Any]

   class EventBus:
       """Central event bus for communication between components"""

       def __init__(self):
           self._subscribers: dict[str, list[Callable[[Event], None]]] = {}

       def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
           """Subscribe to an event type"""
           if event_type not in self._subscribers:
               self._subscribers[event_type] = []
           self._subscribers[event_type].append(callback)

       def publish(self, event: Event) -> None:
           """Publish an event to all subscribers"""
           if event.type not in self._subscribers:
               return

           for callback in self._subscribers[event.type]:
               callback(event)
   ```

   Idea: Redesign the Core Bot Class

   ```python
   class KrakenInfinityGridBot:
       """
       Orchestrates the trading bot's components but delegates specific
       responsibilities to specialized classes.
       """

       def __init__(self, config: dict, db_config: dict, dry_run: bool = False):
           # Create components with dependency injection
           self.event_bus = EventBus()
           self.state_machine = StateMachine()

           # Infrastructure components
           self.db = DatabaseService(**db_config)
           self.rest_api = KrakenRestClient(config["key"], config["secret"])
           self.ws_client = WebsocketClient(
               key=config["key"],
               secret=config["secret"],
               event_bus=self.event_bus
           )

           # Application services
           self.config_service = ConfigService(self.db, config)
           self.order_service = OrderService(
               rest_api=self.rest_api,
               db=self.db,
               event_bus=self.event_bus,
               config=self.config_service
           )

           # Create the appropriate strategy based on config
           strategy_type = config["strategy"]
           self.strategy = self._create_strategy(strategy_type, config)

           # Setup event subscriptions
           self._setup_event_handlers()

       def _create_strategy(self, strategy_type, config):
           strategies = {
               "SWING": SwingStrategy,
               "GridHODL": GridHodlStrategy,
               "GridSell": GridSellStrategy,
               "cDCA": CDCAStrategy
           }

           if strategy_type not in strategies:
               raise ValueError(f"Unknown strategy type: {strategy_type}")

           return strategies[strategy_type](
               order_service=self.order_service,
               config=self.config_service,
               event_bus=self.event_bus
           )

       def _setup_event_handlers(self):
           # Subscribe to events
           self.event_bus.subscribe("ticker_update", self.strategy.on_ticker_update)
           self.event_bus.subscribe("order_filled", self.strategy.on_order_filled)
           self.event_bus.subscribe("order_canceled", self.strategy.on_order_canceled)
           # etc.

       async def run(self):
           """Start the bot"""
           # Handle signals
           self._setup_signal_handlers()

           # Start components
           await self.ws_client.connect()

           # Subscribe to channels
           await self.ws_client.subscribe_ticker(self.config_service.symbol)
           await self.ws_client.subscribe_executions()

           # Wait for shutdown
           await self.state_machine.wait_for_shutdown()
   ```

   Idea: Define clear interfaces

   ... allowing potential usage of other exchanges and backtesting (instead of
   mocking as it is currently done)

   ```Python
   from abc import ABC, abstractmethod
   from typing import dict, Any

   class IOrderService(ABC):
       """Interface for order management operations"""

       @abstractmethod
       async def place_buy_order(self, price: float, volume: float) -> dict[str, Any]:
           pass

       @abstractmethod
       async def place_sell_order(self, price: float, volume: float) -> dict[str, Any]:
           pass

       @abstractmethod
       async def cancel_order(self, txid: str) -> bool:
           pass

       @abstractmethod
       async def get_order_details(self, txid: str) -> dict[str, Any]:
           pass

   class IStrategy(ABC):
       """Interface for trading strategies"""

       @abstractmethod
       def on_ticker_update(self, event: Event) -> None:
           pass

       @abstractmethod
       def on_order_filled(self, event: Event) -> None:
           pass

       @abstractmethod
       def on_order_canceled(self, event: Event) -> None:
           pass

       @abstractmethod
       async def check_price_range(self) -> None:
           pass
   ```

### Reliability Problems

1. **Overly Broad Exception Handling**: Multiple instances of catching generic
   Exception with comments like # noqa: BLE001. This masks specific errors and
   makes debugging difficult.
2. **Inconsistent Error Recovery**: Some errors terminate the bot, others log
   warnings, creating unpredictable behavior.
3. **Missing Retry Mechanisms**: API calls could fail due to rate limiting or network
   issues, but many calls lack proper retry mechanisms.
4. **Poor Shutdown Handling**: The shutdown logic is scattered and complex,
   making it hard to ensure proper cleanup during termination.

### Code Quality Concerns

1. **Complex Methods**: The on_message method has multiple code complexity
   violations (noted by # noqa: C901, PLR0912).
2. **Unresolved TODOs**: Comments like # FIXME: Check if this can still be reached
   indicate technical debt.
3. **Magic Strings/Numbers**: Many hardcoded values like timeouts
   (timedelta(seconds=600)) should be configuration options.
4. **Excessive Commenting**: While documentation is good, some sections are
   over-commented with obvious information rather than explaining the "why".
