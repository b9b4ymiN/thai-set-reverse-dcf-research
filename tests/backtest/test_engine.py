"""
Unit tests for Thai SET Backtest Engine.
"""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime
import pandas as pd
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backtest.engine import (
    ThaiSETBacktestEngine,
    BacktestConfig,
    EnginePerformanceMetrics,
    BacktestResult,
)


class TestThaiSETBacktestEngine(unittest.TestCase):
    """Test cases for Thai SET Backtest Engine."""

    def setUp(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self._create_test_data()

    def tearDown(self):
        """Clean up test data."""
        self.tmpdir.cleanup()

    def _create_test_data(self):
        """Create minimal test data files."""
        root = Path(self.tmpdir.name)

        # Create snapshot
        snapshot = pd.DataFrame([
            {"Ticker": "TEST.BK", "Sector": "Technology", "Industry": "Software", "WACC": 0.08},
        ])
        snapshot_path = root / "snapshot.csv"
        snapshot.to_csv(snapshot_path, index=False)

        # Create observations
        observations = pd.DataFrame([
            {
                "Ticker": "TEST.BK",
                "Period_Type": "quarterly",
                "Statement_Date": "2024-09-30",
                "Availability_Date": "2024-11-14",
                "Revenue": 100.0,
                "FCF": 12.0,
                "Net_Debt": 25.0,
                "Shares_Issued": 10.0,
                "Diluted_Average_Shares": 10.0,
                "Revenue_Growth": 0.10,
                "ROE": 0.15,
                "Debt_to_Equity": 0.5,
                "PE_Ratio": 15.0,
                "PB_Ratio": 2.0,
                "Market_Cap": 1_000_000_000,
            },
        ])
        observations_path = root / "observations.csv"
        observations.to_csv(observations_path, index=False)

        # Create price history
        prices = pd.DataFrame([
            {"Date": "2024-01-02", "Ticker": "TEST.BK", "Open": 100, "High": 100, "Low": 100, "Close": 100, "Adj Close": 100, "Volume": 100},
            {"Date": "2024-04-01", "Ticker": "TEST.BK", "Open": 110, "High": 110, "Low": 110, "Close": 110, "Adj Close": 110, "Volume": 100},
            {"Date": "2024-07-01", "Ticker": "TEST.BK", "Open": 120, "High": 120, "Low": 120, "Close": 120, "Adj Close": 120, "Volume": 100},
        ])
        prices_path = root / "prices.csv"
        prices.to_csv(prices_path, index=False)

        # Create benchmark
        benchmark = pd.DataFrame([
            {"Date": "2024-01-02", "Ticker": "^SET.BK", "Open": 100, "High": 100, "Low": 100, "Close": 100, "Adj Close": 100, "Volume": 1000},
            {"Date": "2024-04-01", "Ticker": "^SET.BK", "Open": 102, "High": 102, "Low": 102, "Close": 102, "Adj Close": 102, "Volume": 1000},
            {"Date": "2024-07-01", "Ticker": "^SET.BK", "Open": 104, "High": 104, "Low": 104, "Close": 104, "Adj Close": 104, "Volume": 1000},
        ])
        benchmark_path = root / "benchmark.csv"
        benchmark.to_csv(benchmark_path, index=False)

        self.test_data_paths = {
            'snapshot': str(snapshot_path),
            'observations': str(observations_path),
            'prices': str(prices_path),
            'benchmark': str(benchmark_path),
        }

    def test_config_initialization(self):
        """Test BacktestConfig initialization."""
        config = BacktestConfig(
            max_positions=15,
            initial_capital=2_000_000,
        )

        self.assertEqual(config.max_positions, 15)
        self.assertEqual(config.initial_capital, 2_000_000)
        self.assertEqual(config.rebalance_frequency, 'QE')

    def test_engine_initialization(self):
        """Test engine initializes with test data."""
        config = BacktestConfig(
            observations_path=self.test_data_paths['observations'],
            price_history_path=self.test_data_paths['prices'],
            benchmark_history_path=self.test_data_paths['benchmark'],
            snapshot_path=self.test_data_paths['snapshot'],
            start_date='2024-01-01',
            end_date='2024-12-31',
        )

        engine = ThaiSETBacktestEngine(config)

        self.assertIsNotNone(engine.signal_generator)
        self.assertIsNotNone(engine.portfolio_constructor)
        self.assertIsNotNone(engine.rebalancer)
        self.assertIsNotNone(engine.observations)
        self.assertIsNotNone(engine.prices)
        self.assertIsNotNone(engine.benchmark)

    def test_engine_runs_backtest(self):
        """Test engine can run a complete backtest."""
        config = BacktestConfig(
            observations_path=self.test_data_paths['observations'],
            price_history_path=self.test_data_paths['prices'],
            benchmark_history_path=self.test_data_paths['benchmark'],
            snapshot_path=self.test_data_paths['snapshot'],
            start_date='2024-01-01',
            end_date='2024-12-31',
            max_positions=10,
            top_n=5,
        )

        engine = ThaiSETBacktestEngine(config)
        result = engine.run()

        # Verify result structure
        self.assertIsInstance(result, BacktestResult)
        self.assertIsInstance(result.metrics, EnginePerformanceMetrics)
        self.assertIsInstance(result.equity_curve, pd.DataFrame)
        self.assertIsInstance(result.portfolio_history, list)
        self.assertIsInstance(result.rebalance_history, list)

    def test_metrics_calculation(self):
        """Test performance metrics are calculated correctly."""
        config = BacktestConfig(
            observations_path=self.test_data_paths['observations'],
            price_history_path=self.test_data_paths['prices'],
            benchmark_history_path=self.test_data_paths['benchmark'],
            snapshot_path=self.test_data_paths['snapshot'],
            start_date='2024-01-01',
            end_date='2024-12-31',
        )

        engine = ThaiSETBacktestEngine(config)
        result = engine.run()

        metrics = result.metrics

        # Check metrics are calculated
        self.assertIsInstance(metrics.total_return, float)
        self.assertIsInstance(metrics.sharpe_ratio, float)
        self.assertIsInstance(metrics.max_drawdown, float)
        self.assertIsInstance(metrics.hit_rate, float)

        # Check reasonable ranges
        self.assertGreaterEqual(metrics.hit_rate, 0.0)
        self.assertLessEqual(metrics.hit_rate, 100.0)
        self.assertLessEqual(metrics.max_drawdown, 0.0)  # Drawdowns are negative

    def test_equity_curve_structure(self):
        """Test equity curve has correct structure."""
        config = BacktestConfig(
            observations_path=self.test_data_paths['observations'],
            price_history_path=self.test_data_paths['prices'],
            benchmark_history_path=self.test_data_paths['benchmark'],
            snapshot_path=self.test_data_paths['snapshot'],
            start_date='2024-01-01',
            end_date='2024-12-31',
        )

        engine = ThaiSETBacktestEngine(config)
        result = engine.run()

        equity_curve = result.equity_curve

        if not equity_curve.empty:
            # Check columns
            self.assertIn('Date', equity_curve.columns)
            self.assertIn('Portfolio_Value', equity_curve.columns)
            self.assertIn('Portfolio_Return', equity_curve.columns)
            self.assertIn('Benchmark_Return', equity_curve.columns)
            self.assertIn('Active_Return', equity_curve.columns)

            # Check data types
            self.assertTrue(pd.api.types.is_datetime64_any_dtype(equity_curve['Date']))
            self.assertTrue(pd.api.types.is_numeric_dtype(equity_curve['Portfolio_Return']))


class TestEnginePerformanceMetrics(unittest.TestCase):
    """Test cases for EnginePerformanceMetrics."""

    def test_metrics_dataclass(self):
        """Test EnginePerformanceMetrics can be instantiated."""
        metrics = EnginePerformanceMetrics(
            total_return=0.15,
            annualized_return=0.12,
            benchmark_return=0.08,
            active_return=0.07,
            volatility=0.15,
            benchmark_volatility=0.12,
            tracking_error=0.08,
            sharpe_ratio=0.8,
            sortino_ratio=1.2,
            information_ratio=0.5,
            max_drawdown=-0.10,
            max_drawdown_duration=50,
            avg_drawdown=-0.03,
            total_trades=100,
            avg_turnover=0.35,
            total_transaction_costs=5000.0,
            hit_rate=60.0,
            win_count=8,
            loss_count=5,
            num_periods=13,
            profitable_periods=8,
        )

        self.assertEqual(metrics.total_return, 0.15)
        self.assertEqual(metrics.sharpe_ratio, 0.8)
        self.assertEqual(metrics.hit_rate, 60.0)


if __name__ == '__main__':
    unittest.main()
