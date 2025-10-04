# Integration Tests Improvement Plan

## Current State Analysis

The existing integration tests have several strengths but also areas for improvement:

### Strengths

- ✅ **Clear separation**: Exchange-specific tests are isolated in `kraken_exchange/` directory
- ✅ **Comprehensive coverage**: Tests cover all major trading scenarios across strategies
- ✅ **Mocking approach**: External dependencies are properly mocked to avoid real trades
- ✅ **Helper patterns**: `KrakenTestManager` centralizes test logic and setup

### Current Issues

- ❌ **High code duplication**: Similar test patterns repeated across strategy files
- ❌ **Kraken-specific coupling**: Test logic is tightly coupled to Kraken implementation
- ❌ **Hard-coded test data**: Expectations are embedded in test files, making maintenance difficult
- ❌ **Limited reusability**: Cannot easily add new exchanges or extend to new trading pairs
- ❌ **Inconsistent testing**: Different tests may validate different aspects or use different approaches

## Proposed Improvements

### 1. Exchange-Agnostic Framework

**Problem**: Current tests are tightly coupled to Kraken-specific implementation.

**Solution**: Create a base framework that can work with any exchange.

```python
# Base class for all exchange test managers
class BaseIntegrationTestManager(ABC):
    async def trigger_prepare_for_trading(self, initial_ticker: float) -> None
    async def trigger_shift_up_buy_orders(self, new_price: float) -> None
    async def trigger_fill_buy_order(self, trigger_price: float) -> None
    # ... common interface methods

# Exchange-specific implementations
class KrakenIntegrationTestManager(BaseIntegrationTestManager):
    # Kraken-specific implementation

class BinanceIntegrationTestManager(BaseIntegrationTestManager):
    # Future Binance-specific implementation
```

**Benefits**:

- Consistent testing approach across all exchanges
- Easy to add new exchanges
- Shared test scenarios and validation logic

### 2. Structured Test Data Management

**Problem**: Test expectations are hard-coded in test files, making them difficult to maintain.

**Solution**: Extract test data into structured, reusable models.

```python
# Before: Hard-coded in test files
@pytest.mark.parametrize(
    ("symbol", "expectations"),
    [
        (
            "XBTUSD",
            {
                "initial_ticker": 50_000.0,
                "1_check_initial_n_buy_orders": {
                    "prices": (49_504.9, 49_014.7, ...),
                    # ... lots of hard-coded data
                }
            }
        )
    ]
)

# After: Structured data models
class StrategyTestExpectations(BaseModel):
    initial_ticker: float
    initial_orders: OrderExpectation
    shift_up_orders: PriceActionExpectation
    fill_buy_order: PriceActionExpectation
    # ... structured expectations

KRAKEN_TEST_SUITE = ExchangeTestSuite(
    exchange_name="Kraken",
    trading_pairs=[...],
    strategy_expectations={...}
)
```

**Benefits**:

- Centralized test data management
- Type safety with Pydantic models
- Easy to add new trading pairs or modify expectations
- Reusable across different test files

### 3. Scenario-Based Testing

**Problem**: Each test file duplicates similar test workflows.

**Solution**: Create reusable test scenarios that can be applied to any strategy/exchange.

```python
# Before: Duplicated test methods
async def test_kraken_gridhodl_initial_setup(...):
    # Setup code
    # Trigger initial setup
    # Validate orders

async def test_kraken_gridsell_initial_setup(...):
    # Same setup code
    # Same trigger logic
    # Same validation logic

# After: Reusable scenarios
class IntegrationTestScenarios:
    async def scenario_initial_setup(self, expectations: StrategyTestExpectations):
        # Common setup logic for all strategies/exchanges

    async def scenario_buy_order_fill(self, expectations: StrategyTestExpectations):
        # Common buy order fill logic

    async def run_complete_strategy_test(self, expectations: StrategyTestExpectations):
        # Runs all applicable scenarios in order
```

**Benefits**:

- Eliminates code duplication
- Consistent test coverage across strategies
- Easy to add new scenarios
- Modular testing approach

### 4. Parameterized Test Generation

**Problem**: Adding new trading pairs or strategies requires manual test updates.

**Solution**: Generate test parameters automatically from configuration.

```python
# Before: Manual parameter definition
@pytest.mark.parametrize(
    ("symbol", "expectations"),
    [
        ("XBTUSD", {...}),
        ("AAPLxUSD", {...}),
        # Must manually add each new pair
    ]
)

# After: Automatic parameter generation
TEST_PARAMETERS = create_test_parameters_from_suite(
    KRAKEN_TEST_SUITE,
    strategies=["GridHODL", "GridSell", "SWING", "cDCA"]
)

@pytest.mark.parametrize("symbol,strategy,expectations", TEST_PARAMETERS)
```

**Benefits**:

- Automatic test coverage for new trading pairs
- Reduced maintenance burden
- Consistent parameter naming and structure

### 5. Improved Test Organization

**Problem**: Current structure mixes exchange-specific and common testing logic.

**Solution**: Reorganize into a cleaner hierarchy.

```
tests/integration/
├── framework/                    # Exchange-agnostic framework
│   ├── __init__.py
│   ├── base_test_manager.py     # Abstract base classes
│   ├── test_data.py             # Data models and test suites
│   ├── test_scenarios.py        # Reusable test scenarios
│   └── example_refactored_tests.py  # Example usage
├── exchanges/                   # Exchange-specific implementations
│   ├── kraken/
│   │   ├── __init__.py
│   │   ├── test_manager.py      # KrakenIntegrationTestManager
│   │   ├── mock_api.py          # Kraken mock implementation
│   │   ├── test_data.py         # Kraken-specific test data
│   │   └── test_*.py            # Kraken integration tests
│   └── binance/                 # Future exchange
│       ├── __init__.py
│       ├── test_manager.py
│       ├── mock_api.py
│       └── test_*.py
├── common/                      # Shared utilities and fixtures
│   ├── __init__.py
│   ├── fixtures.py              # Common test fixtures
│   └── utilities.py             # Test helper functions
└── conftest.py                  # Global test configuration
```

### 6. Mock API Standardization

**Problem**: Current mock APIs are exchange-specific and inconsistent.

**Solution**: Define a standard interface for mock APIs.

```python
class MockExchangeAPI(Protocol):
    def setup_initial_state(self) -> None: ...
    def simulate_ticker_update(self, price: float) -> Dict[str, Any]: ...
    def simulate_order_fill(self, order_id: str) -> Dict[str, Any]: ...
    def get_open_orders(self) -> List[Dict[str, Any]]: ...
    def get_balances(self) -> Dict[str, Dict[str, float]]: ...

# Each exchange implements this protocol
class KrakenMockAPI:
    # Kraken-specific implementation of MockExchangeAPI

class BinanceMockAPI:
    # Binance-specific implementation of MockExchangeAPI
```

**Benefits**:

- Consistent mock behavior across exchanges
- Easier to validate test logic
- Simplified test debugging

## Implementation Strategy

### Phase 1: Framework Foundation

1. ✅ Create `tests/integration/framework/` directory
2. ✅ Implement `BaseIntegrationTestManager` abstract class
3. ✅ Create data models for test expectations
4. ✅ Implement reusable test scenarios

### Phase 2: Kraken Migration

1. 🔄 Migrate existing Kraken tests to use new framework
2. 🔄 Extract Kraken test data into structured format
3. 🔄 Validate that all existing test cases still pass
4. 🔄 Optimize and clean up redundant code

### Phase 3: Extension Preparation

1. ⏭️ Create template for new exchange implementations
2. ⏭️ Document framework usage and extension points
3. ⏭️ Add configuration validation for new exchanges
4. ⏭️ Create helper tools for test data generation

### Phase 4: Future Exchange Support

1. ⏭️ Implement Binance/Coinbase integration tests using framework
2. ⏭️ Validate framework extensibility with different exchange APIs
3. ⏭️ Refine framework based on multi-exchange experience
4. ⏭️ Add cross-exchange validation tests

## Benefits of the Improved Structure

### For Maintainability

- **Centralized test data**: All expectations in one place, easy to update
- **Reduced duplication**: Common scenarios reused across strategies
- **Type safety**: Pydantic models catch configuration errors early
- **Clear separation**: Exchange-specific vs. common logic clearly separated

### For Modularization

- **Pluggable exchanges**: Easy to add new exchanges without touching existing code
- **Reusable scenarios**: Test scenarios work across all exchanges
- **Configurable test suites**: Test data separated from test logic
- **Independent components**: Framework components can be tested separately

### For Multi-Exchange Support

- **Consistent interface**: Same test patterns work for all exchanges
- **Parallel development**: Different exchanges can be developed independently
- **Cross-validation**: Compare behavior across exchanges
- **Unified reporting**: Consistent test results and failure modes

### For Development Workflow

- **Faster feedback**: Run specific scenarios during development
- **Better debugging**: Clear separation between framework and exchange issues
- **Easier onboarding**: New developers can understand test structure quickly
- **Automated coverage**: New trading pairs automatically get full test coverage

## Migration Example

Here's how an existing test would be migrated:

```python
# Before: Kraken-specific, hard-coded test
@pytest.mark.parametrize(
    ("symbol", "expectations"),
    [("XBTUSD", {"initial_ticker": 50_000.0, ...})]
)
async def test_kraken_gridhodl_initial_setup(symbol, expectations, ...):
    # 100+ lines of setup and validation code
    manager = KrakenTestManager(...)
    await manager.initialize_engine()
    await manager.trigger_prepare_for_trading(expectations["initial_ticker"])
    # Validation logic...

# After: Framework-based, reusable test
@pytest.mark.parametrize("symbol,strategy,expectations",
                        create_test_parameters_from_suite(KRAKEN_TEST_SUITE, ["GridHODL"]))
async def test_complete_strategy_workflow(symbol, strategy, expectations, ...):
    # 10 lines of setup, rest handled by framework
    test_manager = KrakenIntegrationTestManager(...)
    await test_manager.initialize_engine()

    scenarios = IntegrationTestScenarios(test_manager)
    await scenarios.run_complete_strategy_test(expectations)
```

This approach provides a solid foundation for scaling to multiple exchanges while maintaining high code quality and test coverage.
