# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) and other agents when working with code
in this repository.

## Overview

`infinity-grid` is a multi-exchange grid trading algorithm (Python 3.11+). It places buy/sell
orders in a grid, buying low and selling high, driven by live exchange WebSocket ticker/execution
events. State is persisted to PostgreSQL (production) or SQLite (development) so the bot can recover
after restarts. It currently supports the Kraken Spot exchange (crypto + tokenized xStocks);
additional exchange adapters are planned. Distributed on PyPI and run via the `infinity-grid` CLI,
typically in a container.

This project is the successor of `kraken-infinity-grid`.

## Commands

All Python tooling goes through `uv`. Never call `python`/`pip` directly.

- **Dev install**: `make dev` (editable install + dev/doc requirements via uv)
- **Run all tests**: `make test` (pytest with `-n auto`, junit xml). `make tests` is an alias.
- **Run only last-failed tests**: `make retest`
- **Run WIP-marked tests**: `make wip` (tests marked `@pytest.mark.wip`)
- **Coverage**: `make coverage` (fails fast with `-x`, writes `coverage.xml` + html)
- **Run a single test**: `uv run pytest tests/unit/test_engine.py::test_name -vv`
- **Lint/format gate**: `prek run` (or `make pre-commit` / `pre-commit run -a`) — runs ruff,
  black, mypy, isort, codespell, gitleaks, hadolint, etc. A change is not done until
  this passes.
- **Build package**: `make build` / `make rebuild`
- **Build Docker image**: `make image` (tags `btschwertfeger/infinity-grid:dev`)
- **Build docs**: `make doc` (Sphinx, in `doc/`)
- **Run locally via compose**: `docker compose up` (app + `postgres:18` service; configured via `.env`)

mypy checks `src` (tests excluded) via the pre-commit hook. It runs with relatively relaxed `Any`
rules but `disallow_untyped_defs`/`disallow_untyped_calls` are enabled, so all signatures need type
hints.

## Architecture

Hexagonal architecture with an event bus, state machine, pluggable strategies, and exchange
adapters behind interfaces. Source lives in `src/infinity_grid/`.

### Wiring & lifecycle

`core/cli.py` (cloup/click) parses options into Pydantic DTOs (`models/configuration.py`:
`BotConfigDTO`, `DBConfigDTO`, `NotificationConfigDTO`, `MetricsConfigDTO`) and constructs
`core/engine.py:BotEngine`.

`BotEngine` is the orchestrator. It owns the `EventBus`, `StateMachine`, `DBConnect`,
`NotificationService`, optional `MetricsServer`, and a single strategy instance built by its
`__strategy_factory` (maps the `strategy` config string to a strategy class). `BotEngine.run()`
installs SIGINT/SIGTERM handlers (which transition the state machine to `SHUTDOWN_REQUESTED`) and
awaits both `strategy.run()` and `state_machine.wait_for_shutdown()` until the first completes, then
`terminate()` tears everything down.

### Event flow (important)

Communication is decoupled through `core/event_bus.py:EventBus` (`subscribe(event_type, cb)` /
`publish(event_type, data)` — synchronous fan-out). The two event types in use are `"on_message"`
and `"notification"`.

The exchange WebSocket adapter receives raw exchange messages, normalizes them, and
`event_bus.publish("on_message", data=...)`. The strategy's `on_message` handler is subscribed to
that event and drives all trading logic. The notification service is subscribed to `"notification"`.
So: **WebSocket adapter → EventBus("on_message") → strategy.on_message → trading decisions →
exchange REST adapter** (order placement) **+ DB persistence**.

### State machine

`core/state_machine.py:States` = `INITIALIZING`, `RUNNING`, `ERROR`, `SHUTDOWN_REQUESTED`, with a
fixed allowed-transitions table enforced by `transition_to`. The strategy gates almost all work on
`state == RUNNING`; entering `ERROR` or `SHUTDOWN_REQUESTED` unblocks `wait_for_shutdown()` and
leads to termination. Components read/transition the shared state machine rather than calling each
other directly.

### Strategies

All inherit from `strategies/grid_base.py:GridStrategyBase` (the large core file holding the grid
logic: orderbook sync, buy/sell order placement, shifting orders up, arbitrage handling, max-
investment checks, status updates). Concrete strategies override behavior:

- **GridHODL** (`grid_hodl.py`): accumulates base currency, sells slightly less than bought.
- **GridSell** (`grid_sell.py`): liquidates the full bought amount each cycle.
- **SWING** (`swing.py`): extends GridHODL with swing-selling on large upward moves.
- **cDCA** (`c_dca.py`): continuous DCA with grid characteristics (no paired sells).

To add a strategy: subclass `GridStrategyBase`, implement the required hooks, and register it in
`BotEngine.__strategy_factory` (engine.py).

### Exchange adapters & interfaces

Adapters implement `interfaces/exchange.py` (`IExchangeRESTService`,
`IExchangeWebSocketService`) and are resolved at runtime by
`adapters/exchange_registry.py:ExchangeAdapterRegistry.get_rest_adapter` /
`get_websocket_adapter` keyed by the `exchange` config value. The Kraken implementation is in
`adapters/exchanges/kraken.py` (REST + WebSocket service adapters), wrapping `python-kraken-sdk`
(an optional extra: `infinity-grid[kraken]`). The SDK is lazily imported so the core package does
not hard-depend on any single exchange (see `tests/unit/test_lazy_import.py`).

To add an exchange: implement both interfaces, add exchange-specific schemas to `models/exchange.py`,
register the adapter, and extend config validation in `models/configuration.py`.

### Persistence & services

`services/database.py:DBConnect` and `infrastructure/database.py` (SQLAlchemy 2.0 models) provide
table-class operations (orderbook, etc.). DB operations are synchronous. `services/notification_service.py`

- `adapters/notification.py` handle Telegram notifications via the `"notification"` event.
  `services/metrics_service.py:MetricsServer` is an optional metrics endpoint.

## Tests

- `tests/unit/` — isolated component tests (engine, event bus, state machine, config models, db,
  adapters, strategies), mocking external systems.
- `tests/integration/` — wires real components together against a SQLite DB and a **mocked**
  python-kraken-sdk to simulate ticker/execution events end-to-end across all four strategies. It
  does NOT hit the live Kraken API. See `tests/integration/README.md` for the covered scenarios.
- `tests/acceptance/` — higher-level checks.
- pytest markers: `asyncio`, `integration`, `wip`, `acceptance` (defined in `pyproject.toml`).

Always add/update tests alongside code changes; tests mirror the source layout.

## Conventions

- Methods use `self: Self`.
- Pydantic v2 for config/data validation and serialization.
- `async`/`await` for WebSocket and I/O; trading/DB logic is synchronous within `on_message`.
- Custom exceptions live in `exceptions.py`.
- Module-level `LOG = getLogger(__name__)`; do not use `log.warn` (blocked by pre-commit hooks).

## Git & pull requests

Derived from the repository's own history — match it. Never add a Claude/AI
co-author trailer or "Generated with" line to commits or PR bodies.

### Branch names

- kebab-case, short and descriptive (`split-dependencies`, `regroup-tests`,
  `update-citation-file`).
- For issue-driven work, GitHub's auto-format `<issue#>-<slugified-title>` is
  also fine (`403-spottradetruncate-not-working-for-xstocks`).
- Branch off `master`; never commit directly to it.

### Commit & PR titles (they match)

- **Issue-driven change:** `Resolve "<exact issue title>"` — quote the issue
  title verbatim, preserving its capitalization and any backticks
  (e.g. `Resolve "`spot.Trade.truncate` not working for xStocks"`).
- **Everything else** (housekeeping, CI, config, refactors): a short imperative
  phrase, no trailing period (`Update tests`, `Improve test suite`,
  `Extract dev-dependencies`, `Fix CI build and update pre-commit hooks`).
- Do **not** use Conventional Commits prefixes (`feat:`, `fix:`, `chore:`) — the
  owner's own commits don't.

### PR bodies

- Keep them minimal: one or two sentences stating what changed and why.
- For larger changes, use `# Summary` or `## <topic>` headers with bullet lists
  of the notable changes.
- End issue-linked PRs with `Closes #<n>` on its own line.

### Assignees

Always set the repository owner (`btschwertfeger`) as the assignee on every PR
created on their behalf. `gh pr edit --add-assignee` may abort on the
projects-classic GraphQL warning — if so, apply via REST:
`gh api -X POST repos/<owner>/<repo>/issues/<pr#>/assignees -f "assignees[]=btschwertfeger"`.

### Labels (apply to both issues and PRs)

Pick the label(s) that match; multiple are fine (e.g. `dependencies` + `github_actions`).

- `bug` — something isn't working
- `enhancement` — new feature or request
- `documentation` — docs improvements or additions
- `chore` — technical debt, setup, typos, CI/workflow/tooling maintenance
- `question` — further information is requested
- `dependencies` — updates a dependency file
- `github_actions` — updates GitHub Actions / workflow code
- `docker` — updates Docker code
- `duplicate`, `good first issue`, `help wanted`, `wontfix`, `layer 8 problem` — as applicable
