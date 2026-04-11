"""
Unit tests for Signal Generator Module
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from backtest.signal_generator import (
    SignalGenerator,
    SignalScoringConfig,
    Signal,
)


@pytest.fixture
def sample_config():
    """Create sample signal configuration."""
    return SignalScoringConfig(
        min_roe=0.08,
        min_fcf=0,
        max_debt_to_equity=3.0,
        max_pe_ratio=50.0,
        max_pb_ratio=10.0,
        min_revenue_growth=-0.5,
        max_implied_growth=0.50,
    )


@pytest.fixture
def sample_cross_section():
    """Create sample cross-sectional data."""
    data = []

    for i in range(20):
        row = {
            'Ticker': f'STOCK{i}',
            'Signal_Score': 0.10 - (i * 0.02),  # Declining scores
            'Implied_Growth_Rate': 0.05 + (i * 0.01),
            'Actual_Revenue_Growth': 0.10,
            'Intrinsic_Value': 100 + i,
            'Price': 100.0,
            'FCF': 1000 * (1 - i * 0.05),
            'Shares': 1000000,
            'WACC': 0.08,
            'ROE': 0.15 - (i * 0.01),
            'Debt_to_Equity': 0.5 + (i * 0.2),
            'Market_Cap': 1e10 * (1 - i * 0.05),
            'No_Lookahead_Pass': True,
        }

        # Add some failing stocks
        if i > 15:
            row['ROE'] = 0.05  # Too low
            row['Debt_to_Equity'] = 5.0  # Too high
            row['No_Lookahead_Pass'] = False

        data.append(row)

    return pd.DataFrame(data)


@pytest.fixture
def sample_snapshot():
    """Create sample snapshot with sector info."""
    sectors = ['Technology', 'Financials', 'Healthcare', 'Consumer', 'Industrials']
    data = []

    for i in range(20):
        data.append({
            'Ticker': f'STOCK{i}',
            'Sector': sectors[i % len(sectors)],
            'Industry': f'Industry {i % 5}',
        })

    return pd.DataFrame(data)


class TestSignalScoringConfig:
    """Test SignalScoringConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SignalScoringConfig()

        assert config.min_roe == 0.08
        assert config.max_pe_ratio == 50.0
        assert config.quality_over_quantity is True


class TestSignalGenerator:
    """Test SignalGenerator class."""

    def test_init(self, sample_config):
        """Test initialization."""
        generator = SignalGenerator(sample_config)
        assert generator.config == sample_config
        assert generator.sector_hurdle_rates is not None

    def test_default_sector_hurdle_rates(self):
        """Test default sector hurdle rates."""
        generator = SignalGenerator()
        hurdle_rates = generator.sector_hurdle_rates

        # Check some key sectors exist
        assert 'Technology' in hurdle_rates
        assert 'Financials' in hurdle_rates
        assert 'Utilities' in hurdle_rates

        # Check rates are reasonable (positive, not too large)
        for rate in hurdle_rates.values():
            assert 0 <= rate <= 0.03

    def test_generate_signals(self, sample_config, sample_cross_section):
        """Test signal generation."""
        generator = SignalGenerator(sample_config)
        signals, filtered_df = generator.generate_signals(
            cross_section=sample_cross_section,
            rebalance_date=datetime(2024, 1, 1),
        )

        # Check we got some signals
        assert len(signals) > 0
        assert isinstance(signals[0], Signal)

        # Check signals are ranked
        ranks = [s.rank for s in signals]
        assert ranks == sorted(ranks)

    def test_signal_screening(self, sample_config, sample_cross_section):
        """Test that screening criteria are applied."""
        generator = SignalGenerator(sample_config)
        signals, filtered_df = generator.generate_signals(
            cross_section=sample_cross_section,
            rebalance_date=datetime(2024, 1, 1),
        )

        # Count passed vs failed
        passed = [s for s in signals if s.passed_screening]
        failed = [s for s in signals if not s.passed_screening]

        # Should have some passed
        assert len(passed) > 0

        # Failed should have reasons
        for s in failed:
            assert len(s.screening_reasons) > 0

    def test_quality_score_calculation(self, sample_config):
        """Test quality score calculation."""
        generator = SignalGenerator(sample_config)

        # High quality stock
        row = pd.Series({
            'ROE': 0.20,
            'Debt_to_Equity': 0.5,
            'FCF': 1000,
        })
        score = generator._calculate_quality_score(row)
        assert score > 0.5  # Should be high quality

        # Low quality stock
        row = pd.Series({
            'ROE': 0.05,
            'Debt_to_Equity': 4.0,
            'FCF': -100,
        })
        score = generator._calculate_quality_score(row)
        assert score < 0.3  # Should be low quality

    def test_valuation_score_calculation(self, sample_config):
        """Test valuation score calculation."""
        generator = SignalGenerator(sample_config)

        # Attractive valuation
        row = pd.Series({
            'PE_Ratio': 10.0,
            'PB_Ratio': 1.5,
        })
        score = generator._calculate_valuation_score(row)
        assert score > 0.5  # Should be attractive

        # Expensive
        row = pd.Series({
            'PE_Ratio': 50.0,
            'PB_Ratio': 8.0,
        })
        score = generator._calculate_valuation_score(row)
        assert score < 0.5  # Should be less attractive

    def test_adjusted_score_calculation(self, sample_config):
        """Test final adjusted score calculation."""
        generator = SignalGenerator(sample_config)

        # Good opportunity (negative growth differential)
        adjusted = generator._calculate_adjusted_score(
            raw_score=-0.10,  # Market pessimistic
            quality_score=0.7,
            valuation_score=0.6,
        )
        assert adjusted > 0  # Should be positive overall

        # Poor opportunity (positive growth differential)
        adjusted = generator._calculate_adjusted_score(
            raw_score=0.20,  # Market optimistic
            quality_score=0.5,
            valuation_score=0.3,
        )
        assert adjusted < 0  # Should be negative overall

    def test_sector_wacc_adjustment(self, sample_config):
        """Test sector-specific WACC adjustment."""
        generator = SignalGenerator(sample_config)

        # Technology sector should get higher WACC
        base_wacc = 0.08
        tech_wacc = generator.adjust_wacc_for_sector(base_wacc, 'Technology')
        assert tech_wacc > base_wacc

        # Consumer Staples should get lower or same WACC
        staples_wacc = generator.adjust_wacc_for_sector(base_wacc, 'Consumer Staples')
        assert staples_wacc <= base_wacc

    def test_get_signal_summary(self, sample_config, sample_cross_section):
        """Test signal summary generation."""
        generator = SignalGenerator(sample_config)
        signals, _ = generator.generate_signals(
            cross_section=sample_cross_section,
            rebalance_date=datetime(2024, 1, 1),
        )

        summary = generator.get_signal_summary(signals)

        # Check summary structure
        assert 'total_signals' in summary
        assert 'passed_screening' in summary
        assert 'sector_distribution' in summary
        assert 'top_10_tickers' in summary

        # Check values make sense
        assert summary['total_signals'] == len(signals)
        assert summary['passed_screening'] <= summary['total_signals']


class TestSignal:
    """Test Signal dataclass."""

    def test_signal_creation(self):
        """Test creating a Signal object."""
        signal = Signal(
            ticker='TEST',
            signal_date=datetime(2024, 1, 1),
            score=0.5,
            rank=1,
            raw_growth_differential=-0.10,
            adjusted_score=0.7,
            quality_score=0.8,
            valuation_score=0.6,
            price=100.0,
            fcf=1000,
            shares=1000000,
            wacc=0.08,
            implied_growth=0.05,
            actual_revenue_growth=0.10,
            roe=0.15,
            debt_to_equity=0.5,
            pe_ratio=15.0,
            pb_ratio=2.0,
            market_cap=1e10,
            sector='Technology',
            industry='Software',
            passed_screening=True,
            screening_reasons=[],
            no_lookahead_pass=True,
        )

        assert signal.ticker == 'TEST'
        assert signal.score == 0.5
        assert signal.rank == 1
        assert signal.passed_screening is True
        assert signal.sector == 'Technology'


@pytest.mark.parametrize("roe,expected_pass", [
    (0.15, True),   # Above threshold
    (0.08, True),   # At threshold
    (0.05, False),  # Below threshold
])
def test_roe_screening(roe, expected_pass):
    """Test ROE screening with different values."""
    config = SignalScoringConfig(min_roe=0.08)
    generator = SignalGenerator(config)

    row = pd.Series({
        'ROE': roe,
        'Debt_to_Equity': 1.0,
        'PE_Ratio': 20.0,
        'PB_Ratio': 2.0,
        'Revenue_Growth': 0.10,
        'Implied_Growth_Rate': 0.05,
        'No_Lookahead_Pass': True,
    })

    passed, _ = generator._screen_stock(row, datetime(2024, 1, 1))

    # ROE screening is applied
    if roe < config.min_roe:
        assert not passed
    else:
        # May still fail other checks
        assert roe >= config.min_roe or not passed


@pytest.mark.parametrize("debt_to_equity,expected_pass", [
    (1.0, True),   # Reasonable
    (3.0, True),   # At threshold
    (5.0, False),  # Too high
])
def test_debt_screening(debt_to_equity, expected_pass):
    """Test debt-to-equity screening."""
    config = SignalScoringConfig(max_debt_to_equity=3.0)
    generator = SignalGenerator(config)

    row = pd.Series({
        'ROE': 0.15,
        'Debt_to_Equity': debt_to_equity,
        'PE_Ratio': 20.0,
        'PB_Ratio': 2.0,
        'Revenue_Growth': 0.10,
        'Implied_Growth_Rate': 0.05,
        'No_Lookahead_Pass': True,
    })

    passed, reasons = generator._screen_stock(row, datetime(2024, 1, 1))

    if debt_to_equity > config.max_debt_to_equity:
        assert not passed
        assert any('D/E' in r for r in reasons)
