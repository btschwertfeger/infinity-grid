# GitHub Copilot Instructions for Infinity Grid Trading Bot

## Project Overview

This is a **multi-exchange infinity grid trading algorithm** written in
Python 3.11+ that implements automated trading strategies using
grid-based approaches. The bot is designed with clean hexagonal architecture,
emphasizing modularity, testability, and extensibility.

The infinity-grid is designed to run in containerized environments and the
repository provides a `Dockerfile`, as well as a `docker-compose.yaml` to run
the application using Docker. Additionally a Helm Chart (`helm/infinity-grid`)
is also provided.

## Architecture & Design Patterns

### Core Architecture

- **Hexagonal Architecture**: Clean separation between domain logic,
  infrastructure, and external adapters
- **Event-Driven Design**: Uses EventBus for decoupled communication between
  components
- **State Machine**: Manages bot lifecycle states (INITIALIZING, RUNNING, ERROR,
  etc.)
- **Strategy Pattern**: Pluggable trading strategies inheriting from
  `GridStrategyBase`
- **Adapter Pattern**: Exchange-specific implementations behind common
  interfaces

### Key Components

```
src/infinity_grid/
├── core/           # Bot engine, CLI, event bus, state management
├── strategies/     # Trading strategy implementations
├── adapters/       # Exchange-specific adapters (Kraken, future exchanges)
├── interfaces/     # Abstract interfaces for exchanges and services
├── models/         # Data models and DTOs using Pydantic
├── services/       # Application services (database, notifications)
└── infrastructure/ # Database schemas and infrastructure concerns
```

## Trading Strategies

### Available Strategies

1. **GridHODL**: Accumulates base currency over time, selling slightly less than
   bought
2. **GridSell**: Liquidates entire bought amount each cycle for immediate
   profits
3. **SWING**: Extends GridHODL with swing selling on significant upward
   movements
4. **cDCA**: Continuous dollar-cost averaging with grid characteristics

### Strategy Implementation Guidelines

- All strategies inherit from `GridStrategyBase`
- Implement required abstract methods for strategy-specific behavior
- Use event bus for communication with other components
- Access configuration via `BotConfigDTO`
- Database operations through provided table interfaces

## Code Style & Conventions

### General Guidelines

- **Type Hints**: Mandatory for all function signatures and class attributes
- **Pydantic Models**: Use for all data validation and serialization
- **Async/Await**: WebSocket operations and I/O-bound tasks
- **Logging**: Use module-level loggers with descriptive messages
- **Error Handling**: Custom exceptions in `exceptions.py`
- **Docstrings**: Documenting functions, classes, and abstractions
- **Comments**: Where really needed, but not like in a 101 tutorial

### Code Organization

- Keep strategy logic in strategy classes
- Use interfaces for external dependencies
- Database operations through dedicated table classes
- Configuration management via `BotConfigDTO`

## Key Development Patterns

### Database Operations

```python
# Use table-specific classes for database operations
self._orderbook_table.add(order_data)
self._orderbook_table.remove(filters={"txid": txid})
orders = self._orderbook_table.get_all()
```

### Exchange Abstraction

```python
# Use interfaces for exchange operations
self._rest_api: IExchangeRESTService
self._ws_client: IExchangeWebSocketService
```

## Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test exchange adapters and database operations
- **Strategy Tests**: Validate trading logic under various market conditions
- **Mocking**: Mock external dependencies (exchanges, databases) for unit tests

## Common Development Tasks

### Adding New Exchange

1. Implement `IExchangeRESTService` and `IExchangeWebSocketService`
2. Create exchange-specific models in `models/exchange.py`
3. Add factory methods in strategy base class
4. Update configuration validation
5. Addition and extension of tests
6. Update of the documentation

### Adding New Strategy

1. Inherit from `GridStrategyBase`
2. Implement required abstract methods
3. Add strategy to factory in `core/engine.py`
4. Update documentation and configuration schemas

### Database Schema Changes

1. Modify models in `infrastructure/database.py`
2. Consider migration strategy for existing data
3. Update related table classes and operations

## Performance Considerations

- WebSocket connections are persistent and managed asynchronously
- Database operations are synchronous but optimized for trading frequency
- Order placement is rate-limited per exchange requirements
- State persistence ensures recovery from interruptions

## Security & Safety

- API keys managed through environment variables
- Dry-run mode available for testing without real trades
- State machine prevents invalid transitions
- Comprehensive error handling and logging

## Dependencies & External Services

- **Exchange APIs**: Currently Kraken, extensible to others
- **Database**: PostgreSQL (production), SQLite (development)
- **Notifications**: Telegram (implemented), Discord (planned)
- **Monitoring**: Structured logging with optional metrics

## Development Environment

- Python 3.11+ required
- Use `pyproject.toml` for dependency management
- CLI tool available via `infinity-grid` command
- Docker support for containerized deployment

## Contributing Guidelines

- Follow clean architecture principles
- Maintain backward compatibility in public interfaces
- Add comprehensive tests for new features
- Update documentation for user-facing changes
- Use type hints and validate inputs with Pydantic

## Key Files to Understand

- `core/engine.py`: Main bot orchestration
- `strategies/grid_base.py`: Base strategy implementation
- `core/state_machine.py`: Bot state management
- `models/configuration.py`: Configuration schemas
- `interfaces/exchange.py`: Exchange abstractions
