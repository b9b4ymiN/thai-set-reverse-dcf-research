"""
Unit tests for Portfolio Constructor Module
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from backtest.portfolio_constructor import (
    PortfolioConstructor,
    EqualWeightConstructor,
    PortfolioConfig,
    PositionSizingMethod,
    DiversificationRule,
    Position,
    Portfolio,
)


@pytest.fixture
def sample_config():
    """Create sample portfolio configuration."""
    return PortfolioConfig(
        max_positions=10,
        min_positions=5,
        sizing_method=PositionSizingMethod.EQUAL_WEIGHT,
        max_position_weight=0.20,
        min_position_weight=0.05,
        max_sector_exposure=0.40,
        max_industry_exposure=0.25,
    )


@pytest.fixture
def sample_signals():
    """Create sample signals for testing."""
    signals = []

    sectors = ['Technology', 'Financials', 'Healthcare', 'Consumer', 'Industrials']

    for i in range(15):
        signal = type('Signal', (), {
            'ticker': f'STOCK{i}',
            'score': 0.5 - (i * 0.03),  # Declining scores
            'rank': i + 1,
            'price': 100.0 + i,
            'sector': sectors[i % len(sectors)],
            'industry': f'Industry {i % 5}',
            'passed_screening': True,
            'quality_score': 0.7 - (i * 0.02),
            'roe': 0.15 - (i * 0.01),
            'debt_to_equity': 0.5 + (i * 0.1),
            'market_cap': 1e10 * (1 - i * 0.05),
            'pe_ratio': 15.0 + i,
            'pb_ratio': 2.0 + i * 0.2,
        })()

        # Add screening reasons for some
        if i > 10:
            signal.passed_screening = False
            signal.screening_reasons = ['Low quality score']

        signals.append(signal)

    return signals


class TestPortfolioConstructor:
    """Test PortfolioConstructor class."""

    def test_init(self, sample_config):
        """Test initialization."""
        constructor = PortfolioConstructor(sample_config)
        assert constructor.config == sample_config

    def test_construct_portfolio_basic(self, sample_config, sample_signals):
        """Test basic portfolio construction."""
        constructor = PortfolioConstructor(sample_config)
        portfolio = constructor.construct_portfolio(
            signals=sample_signals,
            as_of_date=datetime(2024, 1, 1),
        )

        # Check portfolio structure
        assert isinstance(portfolio, Portfolio)
        assert len(portfolio.positions) <= sample_config.max_positions
        assert portfolio.total_weight <= 1.0

        # Check position weights
        for pos in portfolio.positions:
            assert pos.weight <= sample_config.max_position_weight
            assert pos.weight >= sample_config.min_position_weight

    def test_equal_weight_sizing(self, sample_signals):
        """Test equal weight position sizing."""
        config = PortfolioConfig(
            max_positions=5,
            sizing_method=PositionSizingMethod.EQUAL_WEIGHT,
        )
        constructor = PortfolioConstructor(config)
        portfolio = constructor.construct_portfolio(
            signals=sample_signals[:5],
            as_of_date=datetime(2024, 1, 1),
        )

        # Check equal weights
        weights = [pos.weight for pos in portfolio.positions]
        assert all(abs(w - weights[0]) < 0.001 for w in weights)

    def test_sector_diversification(self, sample_signals):
        """Test sector diversification constraints."""
        config = PortfolioConfig(
            max_positions=20,
            max_sector_exposure=0.30,  # Strict sector limit
            require_diversification=True,
        )
        constructor = PortfolioConstructor(config)
        portfolio = constructor.construct_portfolio(
            signals=sample_signals,
            as_of_date=datetime(2024, 1, 1),
        )

        # Check sector exposures
        sector_weights = portfolio.sector_weights
        for sector, weight in sector_weights.items():
            assert weight <= config.max_sector_exposure + 0.01  # Small tolerance

    def test_quality_filter(self, sample_signals):
        """Test quality filtering."""
        config = PortfolioConfig(
            max_positions=20,
            quality_over_quantity=True,
            min_positions=5,
        )
        constructor = PortfolioConstructor(config)
        portfolio = constructor.construct_portfolio(
            signals=sample_signals,
            as_of_date=datetime(2024, 1, 1),
        )

        # Should filter out low-quality signals
        assert len(portfolio.positions) <= len(sample_signals)
        # But should still meet minimum
        assert len(portfolio.positions) >= config.min_positions

    def test_empty_portfolio(self, sample_config):
        """Test handling of no signals."""
        constructor = PortfolioConstructor(sample_config)
        portfolio = constructor.construct_portfolio(
            signals=[],
            as_of_date=datetime(2024, 1, 1),
        )

        assert len(portfolio.positions) == 0
        assert portfolio.cash_weight == 1.0

    def test_turnover_calculation(self, sample_config, sample_signals):
        """Test portfolio turnover calculation."""
        constructor = PortfolioConstructor(sample_config)

        # Create two portfolios
        portfolio1 = constructor.construct_portfolio(
            signals=sample_signals[:10],
            as_of_date=datetime(2024, 1, 1),
        )

        portfolio2 = constructor.construct_portfolio(
            signals=sample_signals[5:15],
            as_of_date=datetime(2024, 2, 1),
        )

        # Calculate turnover
        turnover = constructor.calculate_turnover(portfolio1, portfolio2)

        # Turnover should be between 0 and 1
        assert 0 <= turnover <= 1

    def test_portfolio_to_dataframe(self, sample_config, sample_signals):
        """Test portfolio conversion to DataFrame."""
        constructor = PortfolioConstructor(sample_config)
        portfolio = constructor.construct_portfolio(
            signals=sample_signals,
            as_of_date=datetime(2024, 1, 1),
        )

        df = portfolio.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(portfolio.positions)
        assert 'Ticker' in df.columns
        assert 'Weight' in df.columns
        assert 'Sector' in df.columns


class TestEqualWeightConstructor:
    """Test EqualWeightConstructor class."""

    def test_equal_weight_sizing(self, sample_signals):
        """Test equal weight constructor."""
        constructor = EqualWeightConstructor(max_positions=10)
        portfolio = constructor.construct_portfolio(
            signals=sample_signals[:10],
            as_of_date=datetime(2024, 1, 1),
        )

        # Check equal weights
        weights = [pos.weight for pos in portfolio.positions]
        expected_weight = 1.0 / len(portfolio.positions)

        for weight in weights:
            assert abs(weight - expected_weight) < 0.001


class TestPortfolio:
    """Test Portfolio class."""

    def test_sector_weights(self):
        """Test sector weight calculation."""
        positions = [
            Position('TECH', 0.30, 100.0, sector='Technology'),
            Position('FIN', 0.25, 100.0, sector='Financials'),
            Position('TECH2', 0.20, 100.0, sector='Technology'),
            Position('HLTH', 0.15, 100.0, sector='Healthcare'),
        ]

        portfolio = Portfolio(
            positions=positions,
            as_of_date=datetime(2024, 1, 1),
            total_weight=0.90,
            cash_weight=0.10,
        )

        sector_weights = portfolio.sector_weights

        assert sector_weights['Technology'] == 0.50
        assert sector_weights['Financials'] == 0.25
        assert sector_weights['Healthcare'] == 0.15

    def test_industry_weights(self):
        """Test industry weight calculation."""
        positions = [
            Position('STOCK1', 0.40, 100.0, industry='Software'),
            Position('STOCK2', 0.30, 100.0, industry='Hardware'),
            Position('STOCK3', 0.20, 100.0, industry='Software'),
        ]

        portfolio = Portfolio(
            positions=positions,
            as_of_date=datetime(2024, 1, 1),
            total_weight=0.90,
            cash_weight=0.10,
        )

        industry_weights = portfolio.industry_weights

        assert industry_weights['Software'] == 0.60
        assert industry_weights['Hardware'] == 0.30

    def test_tickers_property(self):
        """Test tickers property."""
        positions = [
            Position('A', 0.5, 100.0),
            Position('B', 0.3, 100.0),
            Position('C', 0.2, 100.0),
        ]

        portfolio = Portfolio(
            positions=positions,
            as_of_date=datetime(2024, 1, 1),
            total_weight=1.0,
            cash_weight=0.0,
        )

        assert portfolio.tickers == ['A', 'B', 'C']
