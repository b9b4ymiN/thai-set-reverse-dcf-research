"""
Unit tests for Rebalancer module.

Tests rebalancing logic, transaction costs, and execution rules.
"""

import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backtest.rebalancer import (
    Rebalancer,
    RebalanceConfig,
    TransactionCostModel,
    Trade,
    RebalanceResult,
)
from backtest.portfolio_constructor import (
    Portfolio,
    Position,
    PortfolioConfig,
    PortfolioConstructor,
)


class TestTransactionCostModel(unittest.TestCase):
    """Test cases for TransactionCostModel."""

    def setUp(self):
        """Set up test fixtures."""
        self.cost_model = TransactionCostModel()

    def test_buy_cost_calculation(self):
        """Test buy side transaction cost calculation."""
        notional = 100_000  # 100k THB trade
        cost = self.cost_model.calculate_buy_cost(notional)

        # Cost should be positive
        self.assertGreater(cost, 0)
        # Should be less than 1% of notional
        self.assertLess(cost, notional * 0.01)

    def test_sell_cost_calculation(self):
        """Test sell side transaction cost calculation."""
        notional = 100_000  # 100k THB trade
        cost = self.cost_model.calculate_sell_cost(notional)

        # Cost should be positive
        self.assertGreater(cost, 0)
        # Should be less than buy cost (no stamp duty)
        buy_cost = self.cost_model.calculate_buy_cost(notional)
        self.assertLess(cost, buy_cost)

    def test_round_trip_cost(self):
        """Test round trip transaction cost."""
        notional = 100_000
        round_trip_cost = self.cost_model.total_round_trip_cost(notional)

        # Round trip should equal buy + sell
        buy_cost = self.cost_model.calculate_buy_cost(notional)
        sell_cost = self.cost_model.calculate_sell_cost(notional)

        self.assertAlmostEqual(round_trip_cost, buy_cost + sell_cost, places=2)

    def test_cost_components(self):
        """Test cost model includes all components."""
        notional = 100_000
        cost = self.cost_model.calculate_buy_cost(notional)

        # Calculate expected components
        commission = notional * self.cost_model.commission_rate
        vat = commission * self.cost_model.vat_rate
        settlement = notional * self.cost_model.settlement_fee_rate
        stamp = notional * self.cost_model.stamp_duty_rate
        slippage = notional * self.cost_model.buy_slippage

        expected = commission + vat + settlement + stamp + slippage
        self.assertAlmostEqual(cost, expected, places=2)


class TestRebalancer(unittest.TestCase):
    """Test cases for Rebalancer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = RebalanceConfig()
        self.cost_model = TransactionCostModel()
        self.rebalancer = Rebalancer(self.config, self.cost_model)

        # Create sample portfolios
        self.date1 = datetime(2024, 1, 1)
        self.date2 = datetime(2024, 4, 1)  # 3 months later

        # Create current portfolio
        self.current_portfolio = Portfolio(
            positions=[
                Position('A', 0.20, 100, sector='Technology'),
                Position('B', 0.20, 50, sector='Financials'),
                Position('C', 0.20, 75, sector='Healthcare'),
                Position('D', 0.20, 200, sector='Technology'),
                Position('E', 0.20, 30, sector='Energy'),
            ],
            as_of_date=self.date1,
            total_weight=1.0,
            cash_weight=0.0,
        )

        # Create target portfolio (different composition)
        self.target_portfolio = Portfolio(
            positions=[
                Position('A', 0.25, 100, sector='Technology'),  # Increased
                Position('B', 0.10, 50, sector='Financials'),  # Decreased
                Position('F', 0.25, 80, sector='Consumer'),  # New
                Position('G', 0.20, 60, sector='Industrials'),  # New
                Position('H', 0.20, 40, sector='Utilities'),  # New
            ],
            as_of_date=self.date2,
            total_weight=1.0,
            cash_weight=0.0,
        )

        # Price data for execution
        self.price_data = {
            'A': 100,
            'B': 50,
            'C': 75,
            'D': 200,
            'E': 30,
            'F': 80,
            'G': 60,
            'H': 40,
        }

    def test_rebalancer_initialization(self):
        """Test Rebalancer initializes correctly."""
        self.assertIsNotNone(self.rebalancer)
        self.assertIsInstance(self.rebalancer.config, RebalanceConfig)
        self.assertIsInstance(self.rebalancer.cost_model, TransactionCostModel)

    def test_should_rebalance_quarterly(self):
        """Test quarterly rebalancing schedule."""
        # Last rebalance 3 months ago - should rebalance
        should_rebalance = self.rebalancer.should_rebalance(
            self.date1,
            self.date2,
        )
        self.assertTrue(should_rebalance)

        # Last rebalance 1 month ago - should not rebalance
        recent_date = datetime(2024, 2, 1)
        should_rebalance = self.rebalancer.should_rebalance(
            self.date1,
            recent_date,
        )
        self.assertFalse(should_rebalance)

    def test_generate_rebalance_trades(self):
        """Test trade generation for rebalancing."""
        trades = self.rebalancer.generate_rebalance_trades(
            self.current_portfolio,
            self.target_portfolio,
            self.date2,
            self.price_data,
        )

        self.assertIsInstance(trades, list)
        self.assertGreater(len(trades), 0)

        # Check trade types
        for trade in trades:
            self.assertIn(trade.action, ['buy', 'sell'])
            self.assertIn(trade.ticker, self.price_data)
            self.assertGreater(trade.notional, 0)

    def test_exit_trades_generated(self):
        """Test exit trades are generated for removed positions."""
        trades = self.rebalancer.generate_rebalance_trades(
            self.current_portfolio,
            self.target_portfolio,
            self.date2,
            self.price_data,
        )

        # Positions C, D, E should be sold (not in target)
        exit_tickers = {t.ticker for t in trades if t.action == 'sell'}
        self.assertIn('C', exit_tickers)
        self.assertIn('D', exit_tickers)
        self.assertIn('E', exit_tickers)

    def test_entry_trades_generated(self):
        """Test entry trades are generated for new positions."""
        trades = self.rebalancer.generate_rebalance_trades(
            self.current_portfolio,
            self.target_portfolio,
            self.date2,
            self.price_data,
        )

        # Positions F, G, H should be bought (new in target)
        entry_tickers = {t.ticker for t in trades if t.action == 'buy'}
        self.assertIn('F', entry_tickers)
        self.assertIn('G', entry_tickers)
        self.assertIn('H', entry_tickers)

    def test_execute_rebalance(self):
        """Test full rebalance execution."""
        result = self.rebalancer.execute_rebalance(
            self.current_portfolio,
            self.target_portfolio,
            self.date2,
            self.price_data,
        )

        self.assertIsInstance(result, RebalanceResult)
        self.assertEqual(result.rebalance_date, self.date2)
        self.assertGreater(len(result.trades), 0)
        self.assertGreater(result.total_transaction_cost, 0)

    def test_turnover_calculation(self):
        """Test turnover rate calculation."""
        result = self.rebalancer.execute_rebalance(
            self.current_portfolio,
            self.target_portfolio,
            self.date2,
            self.price_data,
        )

        # Turnover should be between 0 and 1
        self.assertGreaterEqual(result.turnover_rate, 0)
        self.assertLessEqual(result.turnover_rate, 1)

        # With major changes, turnover should be significant
        self.assertGreater(result.turnover_rate, 0.3)

    def test_execution_summary(self):
        """Test execution summary generation."""
        result = self.rebalancer.execute_rebalance(
            self.current_portfolio,
            self.target_portfolio,
            self.date2,
            self.price_data,
        )

        summary = result.execution_summary

        self.assertIn('total_trades', summary)
        self.assertIn('buy_trades', summary)
        self.assertIn('sell_trades', summary)
        self.assertEqual(summary['total_trades'], len(result.trades))

    def test_rebalance_schedule(self):
        """Test rebalance schedule generation."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        schedule = self.rebalancer.calculate_rebalance_schedule(
            start_date,
            end_date,
        )

        self.assertIsInstance(schedule, list)
        self.assertGreater(len(schedule), 0)
        # Should have quarterly rebalances
        self.assertGreaterEqual(len(schedule), 4)

    def test_annual_cost_estimation(self):
        """Test annual transaction cost estimation."""
        portfolio = self.current_portfolio
        expected_turnover = 0.5  # 50% annual turnover

        annual_cost_pct = self.rebalancer.estimate_annual_transaction_costs(
            portfolio,
            expected_turnover,
        )

        # Cost should be positive but reasonable
        self.assertGreater(annual_cost_pct, 0)
        self.assertLess(annual_cost_pct, 0.05)  # Less than 5%

    def test_rebalance_summary(self):
        """Test rebalance summary generation."""
        result = self.rebalancer.execute_rebalance(
            self.current_portfolio,
            self.target_portfolio,
            self.date2,
            self.price_data,
        )

        summary = self.rebalancer.get_rebalance_summary(result)

        self.assertIn('rebalance_date', summary)
        self.assertIn('turnover_rate', summary)
        self.assertIn('total_transaction_cost', summary)
        self.assertIn('positions_before', summary)
        self.assertIn('positions_after', summary)

        self.assertEqual(
            summary['positions_before'],
            len(self.current_portfolio.positions),
        )
        self.assertEqual(
            summary['positions_after'],
            len(self.target_portfolio.positions),
        )


class TestRebalanceConfig(unittest.TestCase):
    """Test cases for RebalanceConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RebalanceConfig()

        self.assertEqual(config.rebalance_frequency_months, 3)
        self.assertEqual(config.min_portfolio_size, 10)
        self.assertEqual(config.target_portfolio_size, 15)

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RebalanceConfig(
            rebalance_frequency_months=6,  # Semi-annual
            min_portfolio_size=5,
        )

        self.assertEqual(config.rebalance_frequency_months, 6)
        self.assertEqual(config.min_portfolio_size, 5)


if __name__ == '__main__':
    unittest.main()
