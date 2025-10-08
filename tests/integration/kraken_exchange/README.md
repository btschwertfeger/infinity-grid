# Kraken Strategy Integration Tests

The implemented integration tests validate implemented strategies against the
Kraken exchange.

Notable details:

- Uses mocked Kraken API to avoid accidental trades and keep track of balances,
  orders and trades locally.
- The tests are parameterized to run against multiple symbols (e.g. BTCUSD,
  AAPLxUSD) for each strategy.
