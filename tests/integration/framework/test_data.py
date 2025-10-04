# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
Test data models and parameterization for integration tests.

This module provides structured data models for test expectations and
parameterization, making it easier to maintain test data and extend
to new exchanges and trading pairs.
"""

from typing import Dict, List, NamedTuple, Tuple

from pydantic import BaseModel


class OrderExpectation(BaseModel):
    """Expected order state for validation."""

    prices: Tuple[float, ...]
    volumes: Tuple[float, ...]
    sides: Tuple[str, ...]


class PriceActionExpectation(BaseModel):
    """Expected behavior for price action scenarios."""

    trigger_price: float
    expected_orders: OrderExpectation
    no_trigger_price: float | None = None


class StrategyTestExpectations(BaseModel):
    """Complete test expectations for a strategy."""

    initial_ticker: float
    initial_orders: OrderExpectation
    shift_up_orders: PriceActionExpectation
    fill_buy_order: PriceActionExpectation
    ensure_buy_orders: PriceActionExpectation | None = None
    fill_sell_order: PriceActionExpectation | None = None
    rapid_price_drop: PriceActionExpectation | None = None
    rapid_price_rise: PriceActionExpectation | None = None
    max_investment_scenario: Dict[str, float] | None = None


class TradingPairConfig(NamedTuple):
    """Configuration for a trading pair."""

    symbol: str
    base_currency: str
    quote_currency: str
    ws_symbol: str
    min_order_size: float = 0.0001
    price_precision: int = 1
    volume_precision: int = 8


class ExchangeTestSuite(BaseModel):
    """Complete test suite configuration for an exchange."""

    exchange_name: str
    trading_pairs: List[TradingPairConfig]
    strategy_expectations: Dict[str, Dict[str, StrategyTestExpectations]]

    def get_expectations(
        self,
        symbol: str,
        strategy: str,
    ) -> StrategyTestExpectations:
        """Get test expectations for a specific symbol and strategy."""
        return self.strategy_expectations[symbol][strategy]

    def get_trading_pair(self, symbol: str) -> TradingPairConfig:
        """Get trading pair configuration for a symbol."""
        return next(
            (pair for pair in self.trading_pairs if pair.symbol == symbol),
            None,
        )


# ================================================================================
# Kraken-specific test data (can be moved to separate file later)
# ================================================================================

KRAKEN_TRADING_PAIRS = [
    TradingPairConfig(
        symbol="XBTUSD",
        base_currency="BTC",
        quote_currency="USD",
        ws_symbol="BTC/USD",
        min_order_size=0.0001,
        price_precision=1,
        volume_precision=8,
    ),
    TradingPairConfig(
        symbol="AAPLxUSD",
        base_currency="AAPLx",
        quote_currency="USD",
        ws_symbol="AAPLx/USD",
        min_order_size=0.001,
        price_precision=2,
        volume_precision=6,
    ),
]

KRAKEN_GRIDHODL_EXPECTATIONS = {
    "XBTUSD": StrategyTestExpectations(
        initial_ticker=50_000.0,
        initial_orders=OrderExpectation(
            prices=(49_504.9, 49_014.7, 48_529.4, 48_048.9, 47_573.1),
            volumes=(0.00202, 0.0020402, 0.0020606, 0.00208121, 0.00210202),
            sides=("buy", "buy", "buy", "buy", "buy"),
        ),
        shift_up_orders=PriceActionExpectation(
            trigger_price=60_000.0,
            expected_orders=OrderExpectation(
                prices=(59_405.9, 58_817.7, 58_235.3, 57_658.7, 57_087.8),
                volumes=(0.00168333, 0.00170016, 0.00171717, 0.00173434, 0.00175168),
                sides=("buy", "buy", "buy", "buy", "buy"),
            ),
        ),
        fill_buy_order=PriceActionExpectation(
            trigger_price=59_000.0,
            no_trigger_price=59_990.0,
            expected_orders=OrderExpectation(
                prices=(58_817.7, 58_235.3, 57_658.7, 57_087.8, 59_999.9),
                volumes=(0.00170016, 0.00171717, 0.00173434, 0.00175168, 0.00168333),
                sides=("buy", "buy", "buy", "buy", "sell"),
            ),
        ),
        # Additional scenarios can be added here
    ),
    "AAPLxUSD": StrategyTestExpectations(
        initial_ticker=150.0,
        initial_orders=OrderExpectation(
            prices=(148.515, 147.03, 145.54, 144.06, 142.57),
            volumes=(0.673, 0.6798, 0.6866, 0.6936, 0.7006),
            sides=("buy", "buy", "buy", "buy", "buy"),
        ),
        shift_up_orders=PriceActionExpectation(
            trigger_price=180.0,
            expected_orders=OrderExpectation(
                prices=(178.218, 176.44, 174.67, 172.91, 171.16),
                volumes=(0.5611, 0.5669, 0.5727, 0.5786, 0.5846),
                sides=("buy", "buy", "buy", "buy", "buy"),
            ),
        ),
        fill_buy_order=PriceActionExpectation(
            trigger_price=177.0,
            no_trigger_price=179.9,
            expected_orders=OrderExpectation(
                prices=(176.44, 174.67, 172.91, 171.16, 179.99),
                volumes=(0.5669, 0.5727, 0.5786, 0.5846, 0.5556),
                sides=("buy", "buy", "buy", "buy", "sell"),
            ),
        ),
    ),
}

KRAKEN_GRIDSELL_EXPECTATIONS = {
    # Similar structure but with GridSell-specific expectations
    "XBTUSD": StrategyTestExpectations(
        initial_ticker=50_000.0,
        initial_orders=OrderExpectation(
            prices=(49_504.9, 49_014.7, 48_529.4, 48_048.9, 47_573.1),
            volumes=(0.00202, 0.0020402, 0.0020606, 0.00208121, 0.00210202),
            sides=("buy", "buy", "buy", "buy", "buy"),
        ),
        shift_up_orders=PriceActionExpectation(
            trigger_price=60_000.0,
            expected_orders=OrderExpectation(
                prices=(59_405.9, 58_817.7, 58_235.3, 57_658.7, 57_087.8),
                volumes=(0.00168333, 0.00170016, 0.00171717, 0.00173434, 0.00175168),
                sides=("buy", "buy", "buy", "buy", "buy"),
            ),
        ),
        fill_buy_order=PriceActionExpectation(
            trigger_price=59_000.0,
            no_trigger_price=59_990.0,
            expected_orders=OrderExpectation(
                prices=(58_817.7, 58_235.3, 57_658.7, 57_087.8, 59_999.9),
                volumes=(0.00170016, 0.00171717, 0.00173434, 0.00175168, 0.00168333),
                sides=("buy", "buy", "buy", "buy", "sell"),
            ),
        ),
        # GridSell has additional scenarios like sell order fills
        fill_sell_order=PriceActionExpectation(
            trigger_price=60_000.0,
            expected_orders=OrderExpectation(
                prices=(58_817.7, 58_235.3, 57_658.7, 57_087.8, 56_522.5),
                volumes=(0.00170016, 0.00171717, 0.00173434, 0.00175168, 0.0017692),
                sides=("buy", "buy", "buy", "buy", "buy"),
            ),
        ),
    ),
}

# Main test suite configuration
KRAKEN_TEST_SUITE = ExchangeTestSuite(
    exchange_name="Kraken",
    trading_pairs=KRAKEN_TRADING_PAIRS,
    strategy_expectations={
        "XBTUSD": {
            "GridHODL": KRAKEN_GRIDHODL_EXPECTATIONS["XBTUSD"],
            "GridSell": KRAKEN_GRIDSELL_EXPECTATIONS["XBTUSD"],
        },
        "AAPLxUSD": {
            "GridHODL": KRAKEN_GRIDHODL_EXPECTATIONS["AAPLxUSD"],
        },
    },
)
