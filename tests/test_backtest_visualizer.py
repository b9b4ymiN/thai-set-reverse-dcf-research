"""
Tests for Backtest Visualizer Module

Tests visualization functionality for reverse DCF backtest engine
following Damodaran's principles with fixed WACC.
"""

import unittest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import pandas as pd
import numpy as np

from backtest.visualizer import (
    BacktestVisualizer,
    VisualizationConfig,
    BacktestSnapshot,
    PerformanceMetrics,
    export_visualization_data,
)


class TestVisualizationConfig(unittest.TestCase):
    """Test visualization configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = VisualizationConfig()

        self.assertEqual(config.figsize, (12, 8))
        self.assertEqual(config.dpi, 100)
        self.assertTrue(config.show_benchmark)
        self.assertTrue(config.use_fixed_wacc)
        self.assertEqual(config.fixed_wacc, 0.08)
        self.assertEqual(config.risk_free_rate, 0.03)

    def test_custom_config(self):
        """Test custom configuration values."""
        config = VisualizationConfig(
            figsize=(10, 6),
            fixed_wacc=0.10,
            risk_free_rate=0.02,
        )

        self.assertEqual(config.figsize, (10, 6))
        self.assertEqual(config.fixed_wacc, 0.10)
        self.assertEqual(config.risk_free_rate, 0.02)


class TestBacktestSnapshot(unittest.TestCase):
    """Test backtest snapshot dataclass."""

    def test_snapshot_creation(self):
        """Test creating a backtest snapshot."""
        date = datetime(2024, 1, 1)
        snapshot = BacktestSnapshot(
            date=date,
            portfolio_value=1000000,
            benchmark_value=1000000,
            returns=0.05,
            benchmark_returns=0.03,
            positions_held=20,
            cash=50000,
            stock_selection_return=0.02,
            sector_allocation_return=0.01,
            timing_return=0.02,
            portfolio_volatility=0.15,
            max_drawdown=-0.05,
        )

        self.assertEqual(snapshot.date, date)
        self.assertEqual(snapshot.portfolio_value, 1000000)
        self.assertEqual(snapshot.returns, 0.05)
        self.assertEqual(snapshot.positions_held, 20)


class TestBacktestVisualizer(unittest.TestCase):
    """Test backtest visualizer functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = VisualizationConfig()
        self.visualizer = BacktestVisualizer(self.config)

        # Create sample price history
        dates = pd.date_range('2024-01-01', periods=20, freq='Q')
        self.price_history = pd.DataFrame({
            'ADVANC.BK': np.random.randn(20).cumsum() + 100,
            'AOT.BK': np.random.randn(20).cumsum() + 50,
            'BBL.BK': np.random.randn(20).cumsum() + 150,
        }, index=dates)

        # Create sample benchmark history
        self.benchmark_history = pd.DataFrame({
            'SET': np.random.randn(20).cumsum() + 1000,
        }, index=dates)

        # Create sample portfolio snapshots
        self.portfolio_snapshots = []
        for i, date in enumerate(dates):
            snapshot = {
                'date': date,
                'total_value': 1000000 * (1 + np.random.randn() * 0.05),
                'cash': 50000 + np.random.randn() * 10000,
                'positions': [
                    {
                        'ticker': 'ADVANC.BK',
                        'weight': 0.3,
                        'return': np.random.randn() * 0.1,
                        'sector': 'Communication Services',
                    },
                    {
                        'ticker': 'AOT.BK',
                        'weight': 0.2,
                        'return': np.random.randn() * 0.1,
                        'sector': 'Industrials',
                    },
                    {
                        'ticker': 'BBL.BK',
                        'weight': 0.25,
                        'return': np.random.randn() * 0.1,
                        'sector': 'Financial Services',
                    },
                ],
                'volatility': 0.15 + np.random.randn() * 0.02,
                'drawdown': abs(np.random.randn() * 0.05),
            }
            self.portfolio_snapshots.append(snapshot)

        self.rebalance_dates = dates.tolist()

    def test_visualizer_initialization(self):
        """Test visualizer initialization."""
        self.assertIsNotNone(self.visualizer)
        self.assertEqual(self.visualizer.config.fixed_wacc, 0.08)

    def test_prepare_backtest_data(self):
        """Test preparing backtest data."""
        snapshots, metrics = self.visualizer.prepare_backtest_data(
            self.price_history,
            self.benchmark_history,
            self.portfolio_snapshots,
            self.rebalance_dates,
        )

        # Check snapshots
        self.assertIsInstance(snapshots, list)
        self.assertEqual(len(snapshots), len(self.portfolio_snapshots))
        self.assertIsInstance(snapshots[0], BacktestSnapshot)

        # Check metrics
        self.assertIsInstance(metrics, PerformanceMetrics)
        self.assertIsInstance(metrics.total_return, float)
        self.assertIsInstance(metrics.sharpe_ratio, float)

    def test_prepare_backtest_data_empty(self):
        """Test preparing backtest data with empty snapshots."""
        snapshots, metrics = self.visualizer.prepare_backtest_data(
            self.price_history,
            self.benchmark_history,
            [],
            [],
        )

        self.assertEqual(len(snapshots), 0)
        self.assertIsInstance(metrics, PerformanceMetrics)

    def test_generate_summary_table(self):
        """Test generating summary table."""
        snapshots, metrics = self.visualizer.prepare_backtest_data(
            self.price_history,
            self.benchmark_history,
            self.portfolio_snapshots,
            self.rebalance_dates,
        )

        summary_df = self.visualizer.generate_summary_table(metrics, snapshots)

        self.assertIsInstance(summary_df, pd.DataFrame)
        self.assertGreater(len(summary_df), 0)
        self.assertIn('Metric', summary_df.columns)
        self.assertIn('Value', summary_df.columns)

        # Check for key metrics
        metrics_list = summary_df['Metric'].tolist()
        self.assertIn('Total Return', metrics_list)
        self.assertIn('Sharpe Ratio', metrics_list)
        self.assertIn('Max Drawdown', metrics_list)

    def test_prepare_time_series_data(self):
        """Test preparing time series data."""
        snapshots, metrics = self.visualizer.prepare_backtest_data(
            self.price_history,
            self.benchmark_history,
            self.portfolio_snapshots,
            self.rebalance_dates,
        )

        ts_df = self.visualizer.prepare_time_series_data(snapshots)

        self.assertIsInstance(ts_df, pd.DataFrame)
        self.assertEqual(len(ts_df), len(snapshots))
        self.assertIn('Portfolio_Value', ts_df.columns)
        self.assertIn('Benchmark_Value', ts_df.columns)
        self.assertIn('Returns', ts_df.columns)
        self.assertIn('Drawdown', ts_df.columns)

        # Check index is datetime
        self.assertIsInstance(ts_df.index, pd.DatetimeIndex)

    def test_prepare_attribution_analysis(self):
        """Test preparing attribution analysis."""
        snapshots, metrics = self.visualizer.prepare_backtest_data(
            self.price_history,
            self.benchmark_history,
            self.portfolio_snapshots,
            self.rebalance_dates,
        )

        attr_df = self.visualizer.prepare_attribution_analysis(snapshots)

        self.assertIsInstance(attr_df, pd.DataFrame)
        self.assertIn('Stock_Selection', attr_df.columns)
        self.assertIn('Sector_Allocation', attr_df.columns)
        self.assertIn('Timing', attr_df.columns)
        self.assertIn('Cumulative_Stock_Selection', attr_df.columns)
        self.assertIn('Cumulative_Total', attr_df.columns)

    def test_generate_sector_analysis(self):
        """Test generating sector analysis."""
        sector_df = self.visualizer.generate_sector_analysis(
            self.portfolio_snapshots
        )

        self.assertIsInstance(sector_df, pd.DataFrame)
        self.assertGreater(len(sector_df), 0)
        self.assertIn('Sector', sector_df.columns)
        self.assertIn('Avg_Weight', sector_df.columns)
        self.assertIn('Avg_Return', sector_df.columns)

        # Check for expected sectors
        sectors = sector_df['Sector'].tolist()
        self.assertIn('Communication Services', sectors)
        self.assertIn('Industrials', sectors)
        self.assertIn('Financial Services', sectors)

    def test_performance_metrics_calculation(self):
        """Test performance metrics calculation."""
        snapshots, metrics = self.visualizer.prepare_backtest_data(
            self.price_history,
            self.benchmark_history,
            self.portfolio_snapshots,
            self.rebalance_dates,
        )

        # Check return metrics
        self.assertIsInstance(metrics.total_return, float)
        self.assertIsInstance(metrics.annualized_return, float)
        self.assertIsInstance(metrics.cagr, float)

        # Check risk metrics
        self.assertIsInstance(metrics.volatility, float)
        self.assertIsInstance(metrics.sharpe_ratio, float)
        self.assertIsInstance(metrics.max_drawdown, float)

        # Check attribution metrics (Damodaran principles)
        self.assertIsInstance(metrics.avg_growth_differential, float)
        self.assertIsInstance(metrics.wacc_effectiveness, float)
        self.assertIsInstance(metrics.sector_adjustment_impact, float)

    def test_damodaran_fixed_wacc(self):
        """Test that visualizer uses fixed WACC as per Damodaran principles."""
        config = VisualizationConfig(
            use_fixed_wacc=True,
            fixed_wacc=0.08,
        )
        visualizer = BacktestVisualizer(config)

        self.assertTrue(visualizer.config.use_fixed_wacc)
        self.assertEqual(visualizer.config.fixed_wacc, 0.08)


class TestExportVisualizationData(unittest.TestCase):
    """Test exporting visualization data."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

        # Create sample data
        dates = pd.date_range('2024-01-01', periods=10, freq='Q')
        snapshots = []
        for date in dates:
            snapshot = BacktestSnapshot(
                date=date,
                portfolio_value=1000000,
                benchmark_value=1000000,
                returns=0.05,
                benchmark_returns=0.03,
                positions_held=20,
                cash=50000,
            )
            snapshots.append(snapshot)

        self.snapshots = snapshots
        self.metrics = PerformanceMetrics(
            total_return=0.25,
            annualized_return=0.10,
            cagr=0.09,
            volatility=0.15,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            max_drawdown=-0.08,
            calmar_ratio=1.25,
            avg_growth_differential=0.02,
            wacc_effectiveness=0.03,
            sector_adjustment_impact=0.01,
            total_trades=50,
            turnover_rate=0.2,
            avg_hold_period=90,
        )
        self.visualizer = BacktestVisualizer()

    def test_export_visualization_data(self):
        """Test exporting visualization data to CSV files."""
        exported_files = export_visualization_data(
            self.visualizer,
            self.snapshots,
            self.metrics,
            self.temp_dir,
        )

        # Check that files were created
        self.assertIn('summary', exported_files)
        self.assertIn('time_series', exported_files)
        self.assertIn('attribution', exported_files)

        # Check that files exist
        for file_type, file_path in exported_files.items():
            self.assertTrue(Path(file_path).exists(), f"{file_type} file not found")

        # Verify file contents
        summary_df = pd.read_csv(exported_files['summary'])
        self.assertGreater(len(summary_df), 0)
        self.assertIn('Metric', summary_df.columns)
        self.assertIn('Value', summary_df.columns)

        ts_df = pd.read_csv(exported_files['time_series'])
        self.assertEqual(len(ts_df), len(self.snapshots))

        attr_df = pd.read_csv(exported_files['attribution'])
        self.assertEqual(len(attr_df), len(self.snapshots))


class TestAttributionCalculation(unittest.TestCase):
    """Test attribution calculation methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.visualizer = BacktestVisualizer()

    def test_stock_selection_attribution(self):
        """Test stock selection attribution calculation."""
        snapshot = {
            'positions': [
                {'weight': 0.3, 'return': 0.10},
                {'weight': 0.2, 'return': 0.05},
                {'weight': 0.25, 'return': 0.08},
            ]
        }

        attribution = self.visualizer._calculate_stock_selection_attribution(snapshot)

        # Expected: (0.3*0.10 + 0.2*0.05 + 0.25*0.08) / (0.3 + 0.2 + 0.25)
        expected = (0.03 + 0.01 + 0.02) / 0.75
        self.assertAlmostEqual(attribution, expected, places=5)

    def test_stock_selection_attribution_empty(self):
        """Test stock selection attribution with no positions."""
        snapshot = {'positions': []}

        attribution = self.visualizer._calculate_stock_selection_attribution(snapshot)
        self.assertEqual(attribution, 0.0)

    def test_sector_allocation_attribution(self):
        """Test sector allocation attribution calculation."""
        snapshot = {
            'positions': [
                {'weight': 0.3, 'return': 0.10, 'sector': 'Technology'},
                {'weight': 0.2, 'return': 0.05, 'sector': 'Technology'},
                {'weight': 0.25, 'return': 0.08, 'sector': 'Financials'},
            ]
        }

        attribution = self.visualizer._calculate_sector_allocation_attribution(snapshot)

        # Should calculate weighted sector returns
        self.assertIsInstance(attribution, float)

    def test_wacc_effectiveness(self):
        """Test WACC effectiveness calculation."""
        dates = [datetime(2024, 1, 1), datetime(2024, 4, 1)]
        snapshots = [
            BacktestSnapshot(
                date=dates[0],
                portfolio_value=1000000,
                benchmark_value=1000000,
                returns=0.0,
                benchmark_returns=0.0,
                positions_held=20,
                cash=50000,
            ),
            BacktestSnapshot(
                date=dates[1],
                portfolio_value=1100000,  # 10% return
                benchmark_value=1050000,  # 5% return
                returns=0.10,
                benchmark_returns=0.05,
                positions_held=20,
                cash=50000,
            ),
        ]

        effectiveness = self.visualizer._calculate_wacc_effectiveness(snapshots)

        # Expected: 10% - 5% = 5% excess return
        self.assertAlmostEqual(effectiveness, 0.05, places=2)


if __name__ == '__main__':
    unittest.main()
