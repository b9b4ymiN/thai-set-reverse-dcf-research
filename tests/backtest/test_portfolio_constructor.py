"""
Unit tests for PortfolioConstructor module.

Tests portfolio construction, position sizing, and diversification rules.
"""

import unittest
from datetime import datetime
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backtest.portfolio_constructor import (
    PortfolioConstructor,
    EqualWeightConstructor,
    PositionSizingMethod,
    PortfolioConfig,
    Position,
    Portfolio,
)


class MockSignal:
    """Mock Signal object for testing."""

    def __init__(
        self,
        ticker,
        score=1.0,
        price=100.0,
        sector='Technology',
        industry='Software',
        market_cap=1_000_000_000,
        passed_screening=True,
        quality_score=0.5,
    ):
        self.ticker = ticker
        self.score = score
        self.price = price
        self.sector = sector
        self.industry = industry
        self.market_cap = market_cap
        self.passed_screening = passed_screening
        self.quality_score = quality_score
        self.rank = 0  # Will be set by generator


class TestPortfolioConstructor(unittest.TestCase):
    """Test cases for PortfolioConstructor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = PortfolioConfig(max_positions=10, min_positions=5)
        self.constructor = PortfolioConstructor(self.config)
        self.as_of_date = datetime(2024, 3, 31)

        # Create sample signals
        self.sample_signals = [
            MockSignal('A', score=2.0, price=100, sector='Technology'),
            MockSignal('B', score=1.5, price=50, sector='Financials'),
            MockSignal('C', score=1.0, price=75, sector='Healthcare'),
            MockSignal('D', score=0.5, price=200, sector='Technology'),
            MockSignal('E', score=0.3, price=30, sector='Energy'),
        ]

    def test_constructor_initialization(self):
        """Test PortfolioConstructor initializes correctly."""
        self.assertIsNotNone(self.constructor)
        self.assertIsInstance(self.constructor.config, PortfolioConfig)

    def test_construct_portfolio_basic(self):
        """Test basic portfolio construction."""
        portfolio = self.constructor.construct_portfolio(
            self.sample_signals,
            self.as_of_date,
        )

        self.assertIsInstance(portfolio, Portfolio)
        self.assertGreater(len(portfolio.positions), 0)
        self.assertEqual(portfolio.as_of_date, self.as_of_date)

    def test_portfolio_size_limits(self):
        """Test portfolio respects max and min position limits."""
        # Create many signals
        many_signals = [
            MockSignal(f'STOCK{i}', score=1.0, sector='Technology')
            for i in range(20)
        ]

        portfolio = self.constructor.construct_portfolio(
            many_signals,
            self.as_of_date,
        )

        # Should not exceed max_positions
        self.assertLessEqual(len(portfolio.positions), self.config.max_positions)

    def test_equal_weight_positions(self):
        """Test equal weight position sizing."""
        config = PortfolioConfig(
            max_positions=5,
            sizing_method=PositionSizingMethod.EQUAL_WEIGHT,
        )
        constructor = PortfolioConstructor(config)

        portfolio = constructor.construct_portfolio(
            self.sample_signals[:5],
            self.as_of_date,
        )

        # All positions should have roughly equal weight
        weights = [p.weight for p in portfolio.positions]
        expected_weight = 1.0 / len(self.sample_signals[:5])

        for weight in weights:
            self.assertAlmostEqual(weight, expected_weight, places=2)

    def test_sector_diversification(self):
        """Test sector diversification constraints."""
        # Create signals concentrated in one sector
        concentrated_signals = [
            MockSignal(f'TECH{i}', score=1.0, sector='Technology')
            for i in range(10)
        ]
        # Add a few from other sectors
        concentrated_signals.extend([
            MockSignal('FIN1', score=0.9, sector='Financials'),
            MockSignal('HLT1', score=0.8, sector='Healthcare'),
        ])

        config = PortfolioConfig(
            max_positions=10,
            max_sector_exposure=0.50,  # Max 50% in one sector
        )
        constructor = PortfolioConstructor(config)

        portfolio = constructor.construct_portfolio(
            concentrated_signals,
            self.as_of_date,
        )

        # Check sector exposure
        tech_exposure = portfolio.sector_weights.get('Technology', 0)
        self.assertLessEqual(tech_exposure, config.max_sector_exposure)

    def test_position_weight_limits(self):
        """Test maximum position size constraint."""
        config = PortfolioConfig(
            max_positions=5,
            max_position_weight=0.20,  # Max 20% per position
            sizing_method=PositionSizingMethod.EQUAL_WEIGHT,
        )
        constructor = PortfolioConstructor(config)

        portfolio = constructor.construct_portfolio(
            self.sample_signals[:5],
            self.as_of_date,
        )

        for position in portfolio.positions:
            self.assertLessEqual(position.weight, config.max_position_weight)

    def test_empty_portfolio(self):
        """Test handling of empty signal list."""
        portfolio = self.constructor.construct_portfolio(
            [],  # No signals
            self.as_of_date,
        )

        self.assertIsInstance(portfolio, Portfolio)
        self.assertEqual(len(portfolio.positions), 0)
        self.assertEqual(portfolio.cash_weight, 1.0)

    def test_quality_filter(self):
        """Test quality over quantity filtering."""
        # Mix of high and low quality signals
        mixed_signals = [
            MockSignal('HIGH1', score=1.0, quality_score=0.8),
            MockSignal('HIGH2', score=0.9, quality_score=0.7),
            MockSignal('LOW1', score=0.5, quality_score=0.1),
            MockSignal('LOW2', score=0.4, quality_score=0.05),
        ]

        config = PortfolioConfig(
            max_positions=5,
            quality_over_quantity=True,
        )
        constructor = PortfolioConstructor(config)

        portfolio = constructor.construct_portfolio(
            mixed_signals,
            self.as_of_date,
        )

        # Should prefer high quality signals
        self.assertGreater(len(portfolio.positions), 0)
        # Low quality signals should be filtered out
        tickers = [p.ticker for p in portfolio.positions]
        self.assertNotIn('LOW1', tickers)
        self.assertNotIn('LOW2', tickers)

    def test_turnover_calculation(self):
        """Test portfolio turnover calculation."""
        # Create previous portfolio
        prev_signals = [
            MockSignal('A', score=1.0),
            MockSignal('B', score=0.9),
            MockSignal('C', score=0.8),
        ]
        prev_portfolio = self.constructor.construct_portfolio(
            prev_signals,
            datetime(2024, 1, 1),
        )

        # Create new portfolio with some overlap
        new_signals = [
            MockSignal('A', score=1.0),  # Same
            MockSignal('D', score=0.9),  # New
            MockSignal('E', score=0.8),  # New
        ]
        new_portfolio = self.constructor.construct_portfolio(
            new_signals,
            self.as_of_date,
        )

        turnover = self.constructor.calculate_turnover(
            prev_portfolio,
            new_portfolio,
        )

        # Turnover should be between 0 and 1
        self.assertGreater(turnover, 0)
        self.assertLessEqual(turnover, 1)

    def test_portfolio_dataframe(self):
        """Test portfolio to DataFrame conversion."""
        portfolio = self.constructor.construct_portfolio(
            self.sample_signals,
            self.as_of_date,
        )

        df = portfolio.to_dataframe()

        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertIn('Ticker', df.columns)
        self.assertIn('Weight', df.columns)
        self.assertIn('Sector', df.columns)

    def test_sector_weights_calculation(self):
        """Test sector weight calculation."""
        portfolio = self.constructor.construct_portfolio(
            self.sample_signals,
            self.as_of_date,
        )

        sector_weights = portfolio.sector_weights

        self.assertIsInstance(sector_weights, dict)
        self.assertGreater(len(sector_weights), 0)

        # Sum of sector weights should equal total weight
        total_sector_weight = sum(sector_weights.values())
        self.assertAlmostEqual(total_sector_weight, portfolio.total_weight, places=2)


class TestEqualWeightConstructor(unittest.TestCase):
    """Test cases for EqualWeightConstructor."""

    def setUp(self):
        """Set up test fixtures."""
        self.constructor = EqualWeightConstructor(max_positions=10)
        self.as_of_date = datetime(2024, 3, 31)

    def test_equal_weight_initialization(self):
        """Test EqualWeightConstructor uses equal weights."""
        self.assertEqual(
            self.constructor.config.sizing_method,
            PositionSizingMethod.EQUAL_WEIGHT,
        )

    def test_equal_weight_portfolio(self):
        """Test constructed portfolio has equal weights."""
        signals = [
            MockSignal(f'STOCK{i}', score=1.0, sector='Technology')
            for i in range(5)
        ]

        portfolio = self.constructor.construct_portfolio(
            signals,
            self.as_of_date,
        )

        weights = [p.weight for p in portfolio.positions]
        # All weights should be equal
        self.assertTrue(all(abs(w - weights[0]) < 0.01 for w in weights))


if __name__ == '__main__':
    unittest.main()
