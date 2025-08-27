# Integration and System Tests

This directory contains integration and system tests for the project. They
mainly focus on mocking the external dependencies (python-kraken-sdk) in order
to simulate the real-world exchange and the behavior of the system on new ticker
events, executions and so on.

**Main Test Cases**

The following cases are implemented in the integration tests.

| Test Case                                      | GridSell | GridHODL | SWING | DCA |
| ---------------------------------------------- | -------- | -------- | ----- | --- |
| Run through initial setup                      | x        | x        | x     | x   |
| Placement of $n$ buy orders                    | x        | x        | x     | x   |
| Shifting-up buy orders                         | x        | x        | x     | x   |
| Filling a buy order                            | x        | x        | x     | x   |
| Ensuring $n$ open buy orders after X           | x        | x        | x     | x   |
| Filling a sell order                           | x        | x        | x     | -   |
| Rapid price drop                               | x        | x        | x     | x   |
| Rapid price rise                               | x        | x        | x     | x   |
| Max investment reached                         | x        | x        | x     | x   |
| Handling surplus from partly filled buy orders | x        | x        | x     | -   |

**Characteristics**

- Mocks external dependencies to avoid accidental trades (e.g. Kraken API)
- Tests multiple components working together (Focuses on component interactions)
- Tests full system behavior (Verifies business logic flows end-to-end)
- Verifies component interactions (Uses mocks only for external systems)
- Tests database interactions (Uses sqlite database)
- Tests message flow and state changes (Validates state changes)

**It does not include the following**

- Live tests against the live Kraken API
- Tests against the CLI and validating DB (which would be E2E)
- Input validation (as the input is fixed)
