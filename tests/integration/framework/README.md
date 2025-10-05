# Integration Testing Framework

This directory contains a **reusable, exchange-agnostic integration testing framework** for testing trading strategies across different exchanges. The framework provides a structured approach to integration testing with mocked exchange APIs, predefined test scenarios, and type-safe test data models.

## Overview

The integration testing framework is built around three core concepts:

1. **Exchange-Agnostic Base Classes** - Abstract interfaces that define common testing behavior
2. **Reusable Test Scenarios** - Predefined test sequences that validate trading strategy behavior
3. **Type-Safe Test Data Models** - Pydantic models that structure test expectations and parameters

This architecture enables:

- **Consistent testing** across different exchanges and trading pairs
- **Code reusability** through shared test scenarios
- **Easy extension** to new exchanges by implementing base interfaces
- **Type safety** with Pydantic validation of test expectations

## Architecture

### Core Components

```
framework/
├── base_test_manager.py       # Abstract base class for exchange-specific test managers
├── test_scenarios.py          # Collection of reusable test scenarios
└── test_data_models.py        # Pydantic models for test expectations
```

### Component Relationships

```
┌─────────────────────────────────────────────────────┐
│         IntegrationTestScenarios                    │
│  (Exchange-agnostic test scenario orchestration)    │
└──────────────────┬──────────────────────────────────┘
                   │ uses
                   ▼
┌─────────────────────────────────────────────────────┐
│      BaseIntegrationTestManager (ABC)               │
│  (Defines common test workflow interface)           │
└──────────────────┬──────────────────────────────────┘
                   │ implements
                   ▼
┌─────────────────────────────────────────────────────┐
│   Exchange-Specific Test Manager                    │
│   (e.g., KrakenIntegrationTestManager)              │
│   - Initializes exchange-specific mocks             │
│   - Implements exchange-specific behaviors          │
└──────────────────┬──────────────────────────────────┘
                   │ uses
                   ▼
┌─────────────────────────────────────────────────────┐
│        MockExchangeAPI (Protocol)                   │
│   (Exchange-specific API mock implementation)       │
└─────────────────────────────────────────────────────┘
```

## Key Classes

### BaseIntegrationTestManager

**Purpose**: Provides the abstract base for exchange-specific test managers.

**Key Responsibilities**:

- Initializes the `BotEngine` with mocked exchange adapters
- Manages test workflow lifecycle (prepare, execute, verify)
- Defines abstract methods that exchange implementations must provide
- Validates order states and balances

### IntegrationTestScenarios

**Purpose**: Provides reusable, composable test scenarios for trading strategies.

**Key Responsibilities**:

- Orchestrates test sequences for different trading strategies
- Provides high-level scenario methods that combine lower-level test operations
- Ensures consistent testing across strategies and exchanges

**Strategy Test Suites**:

- `run_cdca_scenarios()` - Continuous dollar-cost averaging strategy tests
- `run_gridhodl_scenarios()` - Grid HODL strategy tests
- `run_gridsell_scenarios()` - Grid Sell strategy tests
- `run_swing_scenarios()` - SWING strategy tests

### Test Data Models

**Purpose**: Provide type-safe, structured test expectations using Pydantic.

## How It Works

### 1. Exchange Implementation

To add support for a new exchange, implement the framework interfaces:

```python
# 1. Create exchange-specific mock API
class NewExchangeMockAPI(MockExchangeAPI):
    """Mock implementation of new exchange API."""

    def create_order(self, **kwargs) -> None:
        # Simulate order creation
        pass

    def fill_order(self, txid: str, volume: float | None = None) -> None:
        # Simulate order filling
        pass

    async def simulate_ticker_update(self, callback: Callable, last: float) -> None:
        # Simulate ticker price updates
        pass

    # ... implement other required methods

# 2. Create exchange-specific test manager
class NewExchangeIntegrationTestManager(BaseIntegrationTestManager):
    """Integration test manager for new exchange."""

    def __init__(self, bot_config, db_config, notification_config, exchange_config):
        super().__init__(
            bot_config=bot_config,
            db_config=db_config,
            notification_config=notification_config,
            exchange_config=exchange_config,
            mock_api_type=NewExchangeMockAPI,
        )

    async def trigger_prepare_for_trading(self, initial_ticker: float) -> None:
        # Exchange-specific initialization
        await self._engine.prepare_for_trading()
        # ... simulate initial ticker
```

You can orient the implementation based on existing examples like
`KrakenIntegrationTestManager`.

### 2. Test Data Definition

Define test expectations for your trading pair and strategy:

```python
GRIDHODL_BTCUSD_EXPECTATIONS = GridHODLTestData(
    initial_ticker=50_000.0,
    check_initial_n_buy_orders=OrderExpectation(
        prices=(49_504.9, 49_014.7, 48_529.4, 48_048.9, 47_573.1),
        volumes=(0.02020713, 0.02040824, 0.02061147, 0.02081684, 0.02102437),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    trigger_shift_up_buy_orders=ShiftOrdersExpectation(
        new_price=50_500.0,
        prices=(49_995.0, 49_504.9, 49_019.7, 48_539.2, 48_063.4),
        volumes=(0.02000800, 0.02020713, 0.02040824, 0.02061147, 0.02081684),
        sides=("buy", "buy", "buy", "buy", "buy"),
    ),
    # ... more expectations
)
```

In case they do not differ from the ones used for testing existing exchanges,
you can reuse existing expectation definitions.

### 3. Test Execution

Run the test scenarios in your test functions:

```python
@pytest.mark.integration
@pytest.mark.asyncio
@mock.patch("infinity_grid.adapters.exchanges.NEWEXCHANGE.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_hodl.sleep", return_value=None)
@mock.patch("infinity_grid.strategies.grid_base.sleep", return_value=None)
@pytest.mark.parametrize(
    ("symbol", "test_data"),
    [("XBTUSD", GRIDHODL_BTCUSD_EXPECTATIONS)],
    ids=("BTCUSD",),
)
async def test_gridhodl(
    mock_sleep1: mock.MagicMock,  # noqa: ARG001
    mock_sleep2: mock.MagicMock,  # noqa: ARG001
    mock_sleep3: mock.MagicMock,  # noqa: ARG001
    caplog: pytest.LogCaptureFixture,
    test_manager_factory: Callable,
    symbol: str,
    test_data: GridHODLTestData,
) -> None:
    """
    Test the GridHODL strategy scenarios.
    """
    caplog.set_level(logging.INFO)

    test_manager = test_manager_factory("NEWEXCHANGE", symbol, strategy="GridHODL")
    await test_manager.initialize_engine()

    scenarios = IntegrationTestScenarios(test_manager)
    await scenarios.run_gridhodl_scenarios(test_data)
```

### 4. Test Workflow

Each scenario follows a consistent pattern:

1. **Setup** - Initialize engine with mocked exchange adapters
2. **Action** - Trigger price updates or other events
3. **Verification** - Assert expected order states, balances, and behaviors
4. **Cleanup** - Handled automatically via pytest fixtures

**Example Workflow**:

```
Initialize Engine
    ↓
Prepare for Trading (initial ticker)
    ↓
Check Initial Buy Orders
    ↓
Simulate Price Change (shift orders)
    ↓
Verify Order State
    ↓
Simulate Order Fill
    ↓
Verify Resulting Orders and Balances
    ↓
... continue with more scenarios
```

## Testing Patterns

### Modular Scenario Testing

Test scenarios can be run independently or combined:

```python
# Run complete test suite
await scenarios.run_gridhodl_scenarios(test_data)

# Or run individual scenarios
await scenarios.scenario_prepare_for_trading(50_000.0)
await scenarios.scenario_check_initial_buy_orders(order_expectation)
await scenarios.scenario_fill_buy_order(fill_expectation)
```

### Exchange-Specific Customization

Override methods in your exchange-specific test manager for custom behavior:

```python
class CustomExchangeTestManager(BaseIntegrationTestManager):
    async def trigger_prepare_for_trading(self, initial_ticker: float) -> None:
        # Custom initialization logic
        await super().trigger_prepare_for_trading(initial_ticker)
        # Additional exchange-specific setup
        self._apply_custom_exchange_settings()
```

### Mock API Behavior

The mock API simulates exchange behavior:

- **Order Management** - Track open/filled/cancelled orders
- **Balance Updates** - Update balances on order fills
- **Ticker Simulation** - Trigger price updates to test bot reactions
- **Fee Calculation** - Apply exchange-specific fee structures
- **Order Matching** - Simulate order execution based on price movements

## Extending the Framework

### Adding a New Exchange

1. Implement `MockExchangeAPI` protocol for the exchange
2. Create exchange-specific test manager extending `BaseIntegrationTestManager`
3. Define exchange configuration in `ExchangeTestConfig`
4. Create test files for each strategy on the new exchange

### Adding New Test Scenarios

Add new scenario methods to `IntegrationTestScenarios`:

```python
async def scenario_custom_behavior(self, expectation: CustomExpectation) -> None:
    """Test custom trading behavior."""
    LOG.info("Scenario: Testing custom behavior")
    await self.manager.trigger_custom_action(expectation.param)
    # Verify expected outcome
```

## Best Practices

1. **Keep Scenarios Atomic** - Each scenario should test one specific behavior
2. **Use Type Hints** - Leverage Pydantic for validation and IDE support
3. **Log Clearly** - Use descriptive log messages for debugging
4. **Fail Fast** - Use assertions to catch issues immediately
5. **Clean Test Data** - Keep expectations in separate, well-organized structures
6. **Document Assumptions** - Comment why specific values are expected
7. **Test Edge Cases** - Include scenarios for error conditions and limits
