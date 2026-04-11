"""
Unit tests for SignalGenerator module.

Tests signal generation, screening criteria, and scoring logic.
"""

import unittest
from datetime import datetime
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backtest.signal_generator import (
    SignalGenerator,
    SignalScoringConfig,
    Signal,
)


class TestSignalGenerator(unittest.TestCase):
    """Test cases for SignalGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = SignalScoringConfig()
        self.generator = SignalGenerator(self.config)
        self.rebalance_date = datetime(2024, 3, 31)

        # Sample cross-section data
        self.sample_data = pd.DataFrame([
            {
                'Ticker': 'TEST1',
                'Signal_Score': -0.05,  # Negative = good opportunity
                'Price': 100.0,
                'FCF': 1000000,
                'Shares': 1000000,
                'WACC': 0.08,
                'Implied_Growth_Rate': 0.03,
                'Actual_Revenue_Growth': 0.08,
                'ROE': 0.15,
                'Debt_to_Equity': 0.5,
                'No_Lookahead_Pass': True,
            },
            {
                'Ticker': 'TEST2',
                'Signal_Score': 0.10,  # Positive = expensive
                'Price': 50.0,
                'FCF': 500000,
                'Shares': 500000,
                'WACC': 0.09,
                'Implied_Growth_Rate': 0.15,
                'Actual_Revenue_Growth': 0.05,
                'ROE': 0.10,
                'Debt_to_Equity': 1.5,
                'No_Lookahead_Pass': True,
            },
        ])

        # Sample snapshot with sector data
        self.sample_snapshot = pd.DataFrame([
            {'Ticker': 'TEST1', 'Sector': 'Technology', 'Industry': 'Software'},
            {'Ticker': 'TEST2', 'Sector': 'Financials', 'Industry': 'Banks'},
        ])

    def test_signal_generator_initialization(self):
        """Test SignalGenerator initializes correctly."""
        self.assertIsNotNone(self.generator)
        self.assertIsInstance(self.generator.config, SignalScoringConfig)
        self.assertIsInstance(self.generator.sector_hurdle_rates, dict)

    def test_sector_hurdle_rates_default(self):
        """Test default sector hurdle rates are populated."""
        rates = self.generator._default_sector_hurdle_rates()
        self.assertIn('Technology', rates)
        self.assertIn('Financials', rates)
        self.assertIn('Energy', rates)
        # Technology should have higher hurdle rate (more risk)
        self.assertGreater(rates['Technology'], rates['Financials'])

    def test_generate_signals_basic(self):
        """Test basic signal generation."""
        signals, filtered_df = self.generator.generate_signals(
            self.sample_data,
            self.rebalance_date,
            self.sample_snapshot,
        )

        self.assertIsInstance(signals, list)
        self.assertGreater(len(signals), 0)
        self.assertIsInstance(filtered_df, pd.DataFrame)

    def test_signal_ranking(self):
        """Test signals are properly ranked by score."""
        signals, _ = self.generator.generate_signals(
            self.sample_data,
            self.rebalance_date,
            self.sample_snapshot,
        )

        # Check that ranks are sequential starting from 1
        ranks = [s.rank for s in signals]
        self.assertEqual(ranks, sorted(ranks))
        self.assertEqual(ranks[0], 1)

    def test_screening_quality_filters(self):
        """Test quality screening filters."""
        # Create data with low ROE
        low_quality_data = pd.DataFrame([{
            'Ticker': 'LOWQ',
            'Signal_Score': -0.10,
            'Price': 50.0,
            'FCF': 100000,
            'Shares': 100000,
            'WACC': 0.08,
            'Implied_Growth_Rate': 0.02,
            'Actual_Revenue_Growth': 0.05,
            'ROE': 0.02,  # Below min 8%
            'Debt_to_Equity': 0.5,
            'No_Lookahead_Pass': True,
        }])

        signals, _ = self.generator.generate_signals(
            low_quality_data,
            self.rebalance_date,
        )

        # With quality_over_quantity=True, should fail screening
        if self.generator.config.quality_over_quantity:
            # Should either be filtered out or marked as failed
            if signals:
                self.assertFalse(signals[0].passed_screening)

    def test_screening_debt_filter(self):
        """Test debt-to-equity screening filter."""
        high_debt_data = pd.DataFrame([{
            'Ticker': 'HIGHDEBT',
            'Signal_Score': -0.10,
            'Price': 50.0,
            'FCF': 500000,
            'Shares': 100000,
            'WACC': 0.08,
            'Implied_Growth_Rate': 0.02,
            'Actual_Revenue_Growth': 0.05,
            'ROE': 0.15,
            'Debt_to_Equity': 5.0,  # Above max 3.0
            'No_Lookahead_Pass': True,
        }])

        signals, _ = self.generator.generate_signals(
            high_debt_data,
            self.rebalance_date,
        )

        if signals and self.generator.config.quality_over_quantity:
            self.assertFalse(signals[0].passed_screening)

    def test_quality_score_calculation(self):
        """Test quality score calculation."""
        signals, _ = self.generator.generate_signals(
            self.sample_data,
            self.rebalance_date,
        )

        for signal in signals:
            self.assertIsInstance(signal.quality_score, float)
            self.assertGreaterEqual(signal.quality_score, 0)
            self.assertLessEqual(signal.quality_score, 1)

    def test_adjusted_wacc_for_sector(self):
        """Test WACC adjustment for different sectors."""
        base_wacc = 0.08

        # Technology should get higher hurdle rate
        tech_wacc = self.generator.adjust_wacc_for_sector(
            base_wacc, 'Technology'
        )
        self.assertGreater(tech_wacc, base_wacc)

        # Utilities should get lower hurdle rate
        util_wacc = self.generator.adjust_wacc_for_sector(
            base_wacc, 'Utilities'
        )
        self.assertLess(util_wacc, base_wacc)

        # Unknown sector should get base WACC
        unknown_wacc = self.generator.adjust_wacc_for_sector(
            base_wacc, 'Unknown'
        )
        self.assertEqual(unknown_wacc, base_wacc)

    def test_get_signal_summary(self):
        """Test signal summary statistics."""
        signals, _ = self.generator.generate_signals(
            self.sample_data,
            self.rebalance_date,
            self.sample_snapshot,
        )

        summary = self.generator.get_signal_summary(signals)

        self.assertIn('total_signals', summary)
        self.assertIn('passed_screening', summary)
        self.assertIn('avg_score', summary)
        self.assertIn('sector_distribution', summary)
        self.assertEqual(summary['total_signals'], len(signals))

    def test_no_lookahead_validation(self):
        """Test no-lookahead bias validation."""
        # Data with failed no-lookahead
        lookahead_fail_data = pd.DataFrame([{
            'Ticker': 'LOOKFAIL',
            'Signal_Score': -0.10,
            'Price': 50.0,
            'FCF': 500000,
            'Shares': 100000,
            'WACC': 0.08,
            'Implied_Growth_Rate': 0.02,
            'Actual_Revenue_Growth': 0.05,
            'ROE': 0.15,
            'Debt_to_Equity': 0.5,
            'No_Lookahead_Pass': False,  # Failed validation
        }])

        signals, _ = self.generator.generate_signals(
            lookahead_fail_data,
            self.rebalance_date,
        )

        if signals and self.generator.config.avoid_lookahead_bias:
            self.assertFalse(signals[0].passed_screening)
            self.assertFalse(signals[0].no_lookahead_pass)


class TestSignalScoringConfig(unittest.TestCase):
    """Test cases for SignalScoringConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SignalScoringConfig()

        self.assertEqual(config.min_roe, 0.08)
        self.assertEqual(config.max_debt_to_equity, 3.0)
        self.assertEqual(config.max_pe_ratio, 50.0)
        self.assertTrue(config.quality_over_quantity)
        self.assertTrue(config.avoid_lookahead_bias)

    def test_custom_config(self):
        """Test custom configuration values."""
        config = SignalScoringConfig(
            min_roe=0.10,
            max_debt_to_equity=2.0,
            quality_over_quantity=False,
        )

        self.assertEqual(config.min_roe, 0.10)
        self.assertEqual(config.max_debt_to_equity, 2.0)
        self.assertFalse(config.quality_over_quantity)


if __name__ == '__main__':
    unittest.main()
