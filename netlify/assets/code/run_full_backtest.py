#!/usr/bin/env python3
"""
Run Full Backtest on Thai SET Reverse DCF Strategy

Uses 88 stocks with 20 quarters of fundamental data
Applies Damodaran's methodology with fixed WACC baseline
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import sys

# Add backtest module to path
sys.path.insert(0, str(Path(__file__).parent))

from backtest.engine import BacktestConfig, ThaiSETBacktestEngine
from backtest.signal_generator import SignalScoringConfig
from backtest.portfolio_constructor import PortfolioConfig
from backtest.rebalancer import RebalanceConfig, TransactionCostModel


def load_fundamental_data():
    """Load fundamental data from scraped stocks."""
    print("Loading fundamental data...")

    df = pd.read_csv('data/processed/fundamentals/quarterly/fundamentals.csv')
    print(f"  ✓ Loaded {len(df)} observations")

    # Check unique stocks
    unique_stocks = df['Ticker'].nunique()
    print(f"  ✓ Unique stocks: {unique_stocks}")

    # Check date range
    if 'Fetched_Date' in df.columns:
        df['Fetched_Date'] = pd.to_datetime(df['Fetched_Date'])
        print(f"  ✓ Date range: {df['Fetched_Date'].min()} to {df['Fetched_Date'].max()}")

    return df


def create_backtest_config():
    """Create backtest configuration with Damodaran principles."""

    # Thailand-specific parameters from Phase 2 research
    config = BacktestConfig(
        # Data paths
        observations_path='data/processed/fundamentals/quarterly/fundamentals.csv',
        price_history_path='data/processed/price_history.csv',  # Will create if needed
        benchmark_history_path='data/processed/benchmark.csv',  # Will create if needed

        # Backtest period - use 2021-2026 for recent Thai market data
        start_date='2021-01-01',
        end_date='2025-12-31',
        rebalance_frequency='QE',  # Quarterly end

        # Portfolio settings - Damodaran's "quality over quantity" principle
        max_positions=20,
        min_positions=10,
        position_sizing='equal_weight',  # Start simple

        # Execution
        execution_delay_days=1,
        initial_capital=1_000_000,  # 1M THB

        # Signal generation - Thailand WACC (from Phase 2)
        default_wacc=0.10,  # 10% fixed discount rate (no lookahead bias)
        top_n=15,  # Top 15 stocks

        # Cost model
        include_transaction_costs=True,
    )

    return config


def run_backtest():
    """Run the full backtest."""

    print("\n" + "="*60)
    print("THAI SET REVERSE DCF BACKTEST")
    print("="*60)
    print("\nApplying Damodaran's Principles:")
    print("  • No lookahead bias (fixed WACC)")
    print("  • Quality over quantity (max 20 positions)")
    print("  • Sector diversification")
    print("  • Time-varying awareness (regime analysis)")
    print()

    # Load data
    fundamentals = load_fundamental_data()

    # Create config
    config = create_backtest_config()

    # Initialize engine
    print("\nInitializing backtest engine...")
    engine = ThaiSETBacktestEngine(config)

    # Run backtest
    print("\nRunning backtest...")
    print(f"  Period: {config.start_date} to {config.end_date}")
    print(f"  Rebalancing: {config.rebalance_frequency}")
    print(f"  Max positions: {config.max_positions}")

    try:
        results = engine.run()

        # Print summary
        print("\n" + "="*60)
        print("BACKTEST RESULTS SUMMARY")
        print("="*60)

        if results and hasattr(results, 'metrics'):
            metrics = results.metrics

            print("\nPerformance Metrics:")
            print(f"  CAGR: {metrics.get('cagr', 0):.2%}")
            print(f"  Sharpe Ratio: {metrics.get('sharpe', 0):.2f}")
            print(f"  Sortino Ratio: {metrics.get('sortino', 0):.2f}")
            print(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
            print(f"  Win Rate: {metrics.get('win_rate', 0):.2%}")

            print("\nRegime Analysis:")
            if 'regime_analysis' in metrics:
                for year, year_metrics in metrics['regime_analysis'].items():
                    print(f"  {year}: {year_metrics.get('return', 0):.2%}")

        print(f"\nResults saved to: {config.output_dir}/")
        print("\n✅ Backtest complete!")

        return results

    except Exception as e:
        print(f"\n❌ Error running backtest: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    results = run_backtest()
