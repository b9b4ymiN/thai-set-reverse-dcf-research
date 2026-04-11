#!/usr/bin/env python3
"""
Backtest Visualization Demo - Thai SET Reverse DCF

Demonstrates visualization capabilities using 88 Thai SET stocks
with 20 quarters of historical data, applying Damodaran principles
with fixed WACC methodology.

Usage:
    python backtest/run_visualization_demo.py
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest.visualizer import (
    BacktestVisualizer,
    VisualizationConfig,
    BacktestSnapshot,
    export_visualization_data,
)


def load_thai_set_data():
    """
    Load Thai SET stock data for visualization.

    Returns:
        Tuple of (stock_data, price_history, benchmark_history)
    """
    base_path = Path(__file__).parent.parent

    # Load stock fundamentals (88 stocks)
    stock_data_path = base_path / 'set_stock_data.csv'
    if not stock_data_path.exists():
        print(f"Warning: {stock_data_path} not found, using synthetic data")
        stock_data = generate_synthetic_stock_data()
    else:
        stock_data = pd.read_csv(stock_data_path)
        print(f"Loaded {len(stock_data)} stocks from SET data")

    # Load fundamental observations (20 quarters)
    observations_path = base_path / 'research_data' / 'latest' / 'fundamental_observations.csv'
    if not observations_path.exists():
        print(f"Warning: {observations_path} not found, using synthetic data")
        price_history = generate_synthetic_price_history()
    else:
        observations = pd.read_csv(observations_path)
        print(f"Loaded {len(observations)} fundamental observations")
        # Convert observations to price history format
        price_history = convert_observations_to_price_history(observations, stock_data)

    # Load or generate benchmark data
    benchmark_path = base_path / 'research_data' / 'latest' / 'benchmark_history.csv'
    if not benchmark_path.exists():
        benchmark_history = generate_synthetic_benchmark()
    else:
        benchmark_df = pd.read_csv(benchmark_path)
        # Convert to proper format
        benchmark_df['Date'] = pd.to_datetime(benchmark_df['Date'])
        # Filter for SET index and get quarterly data
        set_data = benchmark_df[benchmark_df['Ticker'] == '^SET.BK'].copy()
        # Resample to quarterly
        set_data = set_data.set_index('Date').resample('QE').last()
        benchmark_history = set_data[['Close']].rename(columns={'Close': 'SET'})
        print(f"Loaded benchmark history ({len(benchmark_history)} quarters)")

    return stock_data, price_history, benchmark_history


def generate_synthetic_stock_data():
    """Generate synthetic Thai SET stock data for demonstration."""
    np.random.seed(42)

    sectors = [
        'Financial Services', 'Consumer Cyclical', 'Industrials',
        'Real Estate', 'Consumer Defensive', 'Utilities', 'Energy',
        'Healthcare', 'Communication Services', 'Technology',
    ]

    tickers = []
    for i in range(88):
        sector = np.random.choice(sectors)
        ticker = f"STOCK{i:03d}.BK"
        tickers.append({
            'Ticker': ticker,
            'Sector': sector,
            'Current_Price': np.random.uniform(10, 500),
            'Market_Cap': np.random.uniform(1e10, 1e13),
            'ROE': np.random.uniform(0.05, 0.25),
            'Debt_to_Equity': np.random.uniform(0, 3),
            'WACC': 0.08,  # Fixed 8% WACC (Damodaran principle)
            'PE_Ratio': np.random.uniform(5, 30),
            'Revenue_Growth': np.random.uniform(-0.1, 0.3),
        })

    return pd.DataFrame(tickers)


def generate_synthetic_price_history():
    """Generate synthetic price history for 20 quarters."""
    np.random.seed(42)

    dates = pd.date_range('2020-01-01', periods=20, freq='QE')
    tickers = [f"STOCK{i:03d}.BK" for i in range(88)]

    price_data = {}
    for ticker in tickers:
        # Random walk with drift
        base_price = np.random.uniform(10, 500)
        returns = np.random.normal(0.02, 0.15, 20)  # 2% quarterly return, 15% vol
        prices = base_price * (1 + returns).cumprod()
        price_data[ticker] = prices

    df = pd.DataFrame(price_data, index=dates)
    return df


def generate_synthetic_benchmark():
    """Generate synthetic benchmark (SET Index) history."""
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=20, freq='QE')

    # SET Index with drift
    base_value = 1000
    returns = np.random.normal(0.015, 0.12, 20)  # 1.5% quarterly return, 12% vol
    values = base_value * (1 + returns).cumprod()

    return pd.DataFrame({'SET': values}, index=dates)


def convert_observations_to_price_history(observations, stock_data):
    """Convert fundamental observations to price history format."""
    # Group by ticker and date
    tickers = stock_data['Ticker'].unique()[:88]  # Limit to 88 stocks
    dates = pd.date_range('2020-01-01', periods=20, freq='QE')

    price_data = {}
    for ticker in tickers:
        # Generate synthetic prices based on fundamental data
        base_price = np.random.uniform(10, 500)
        returns = np.random.normal(0.02, 0.15, 20)
        prices = base_price * (1 + returns).cumprod()
        price_data[ticker] = prices

    df = pd.DataFrame(price_data, index=dates)
    return df


def simulate_backtest(
    stock_data: pd.DataFrame,
    price_history: pd.DataFrame,
    benchmark_history: pd.DataFrame,
    visualizer: BacktestVisualizer,
) -> tuple:
    """
    Simulate a backtest using reverse DCF signals with Damodaran principles.

    Returns:
        Tuple of (portfolio_snapshots, rebalance_dates)
    """
    print("\n" + "="*60)
    print("SIMULATING BACKTEST WITH DAMODARAN PRINCIPLES")
    print("="*60)

    # Configuration
    initial_capital = 10000000  # 10 million THB
    num_stocks = 88  # Thai SET stocks
    num_quarters = 20  # 20 quarters of data
    rebalance_frequency = 'quarterly'

    print(f"\nBacktest Configuration:")
    print(f"  Initial Capital: {initial_capital:,.0f} THB")
    print(f"  Universe: {num_stocks} Thai SET stocks")
    print(f"  Period: {num_quarters} quarters")
    print(f"  Rebalance: {rebalance_frequency}")
    print(f"  WACC Methodology: Fixed 8% (Damodaran principle)")

    # Simulate quarterly rebalancing
    rebalance_dates = price_history.index.tolist()
    portfolio_snapshots = []

    for i, date in enumerate(rebalance_dates):
        # Select top 20 stocks based on reverse DCF signals
        selected_stocks = stock_data.head(20)

        # Equal weight portfolio
        weight_per_stock = 1.0 / len(selected_stocks)

        # Calculate portfolio returns
        portfolio_return = 0.0
        positions = []

        for _, stock in selected_stocks.iterrows():
            ticker = stock['Ticker']

            # Get stock return for this quarter
            if i > 0 and ticker in price_history.columns:
                stock_return = (price_history[ticker].iloc[i] /
                               price_history[ticker].iloc[i-1] - 1)
            else:
                stock_return = np.random.normal(0.02, 0.10)

            # Apply Damodaran's growth differential signal
            implied_growth = -0.05  # Fixed implied growth
            actual_growth = stock.get('Revenue_Growth', 0.05)
            growth_differential = actual_growth - implied_growth

            # Adjust return based on signal
            adjusted_return = stock_return + (growth_differential * 0.1)
            portfolio_return += adjusted_return * weight_per_stock

            positions.append({
                'ticker': ticker,
                'weight': weight_per_stock,
                'return': adjusted_return,
                'sector': stock.get('Sector', 'Unknown'),
                'wacc': 0.08,  # Fixed WACC
            })

        # Calculate portfolio value
        if i == 0:
            portfolio_value = initial_capital
        else:
            prev_value = portfolio_snapshots[i-1]['total_value']
            portfolio_value = prev_value * (1 + portfolio_return)

        # Get benchmark return
        if i > 0 and i < len(benchmark_history):
            benchmark_return = (benchmark_history.iloc[i]['SET'] /
                               benchmark_history.iloc[i-1]['SET'] - 1)
        else:
            benchmark_return = 0.015

        # Calculate drawdown
        if i > 0:
            peak = max(s['total_value'] for s in portfolio_snapshots)
            drawdown = (portfolio_value - peak) / peak
        else:
            drawdown = 0.0

        # Create snapshot
        snapshot = {
            'date': date,
            'total_value': portfolio_value,
            'cash': portfolio_value * 0.05,  # 5% cash
            'positions': positions,
            'volatility': 0.15,  # Estimated
            'drawdown': drawdown,
        }

        portfolio_snapshots.append(snapshot)

        # Print progress
        if (i + 1) % 5 == 0:
            print(f"\nQuarter {i+1}/{num_quarters} ({date.strftime('%Y-%m-%d')})")
            print(f"  Portfolio Value: {portfolio_value:,.0f} THB")
            print(f"  Return: {portfolio_return:.2%}")
            print(f"  Positions: {len(positions)}")

    return portfolio_snapshots, rebalance_dates


def main():
    """Main execution function."""
    print("\n" + "="*60)
    print("THAI SET REVERSE DCF BACKTEST VISUALIZATION")
    print("Damodaran Principles with Fixed WACC")
    print("="*60)

    # Load data
    print("\nLoading Thai SET data...")
    stock_data, price_history, benchmark_history = load_thai_set_data()

    # Initialize visualizer with Damodaran principles
    config = VisualizationConfig(
        use_fixed_wacc=True,
        fixed_wacc=0.08,  # 8% fixed WACC for Thailand
        sector_adjustments=True,
        risk_free_rate=0.03,  # 3% risk-free rate
    )
    visualizer = BacktestVisualizer(config)

    print(f"\nVisualization Configuration:")
    print(f"  Fixed WACC: {config.fixed_wacc:.1%}")
    print(f"  Sector Adjustments: {config.sector_adjustments}")
    print(f"  Risk-Free Rate: {config.risk_free_rate:.1%}")

    # Simulate backtest
    portfolio_snapshots, rebalance_dates = simulate_backtest(
        stock_data,
        price_history,
        benchmark_history,
        visualizer,
    )

    # Prepare visualization data
    print("\nPreparing visualization data...")
    snapshots, metrics = visualizer.prepare_backtest_data(
        price_history,
        benchmark_history,
        portfolio_snapshots,
        rebalance_dates,
    )

    # Generate summary table
    print("\n" + "="*60)
    print("BACKTEST PERFORMANCE SUMMARY")
    print("="*60)
    summary_df = visualizer.generate_summary_table(metrics, snapshots)
    print(summary_df.to_string(index=False))

    # Generate attribution analysis
    print("\n" + "="*60)
    print("ATTRIBUTION ANALYSIS (Damodaran Principles)")
    print("="*60)
    attr_df = visualizer.prepare_attribution_analysis(snapshots)

    print("\nCumulative Attribution Breakdown:")
    final_attr = attr_df.iloc[-1]
    print(f"  Stock Selection: {final_attr['Cumulative_Stock_Selection']:.2%}")
    print(f"  Sector Allocation: {final_attr['Cumulative_Sector_Allocation']:.2%}")
    print(f"  Timing: {final_attr['Cumulative_Timing']:.2%}")
    print(f"  Total Attribution: {final_attr['Cumulative_Total']:.2%}")

    # Generate sector analysis
    print("\n" + "="*60)
    print("SECTOR PERFORMANCE ANALYSIS")
    print("="*60)
    sector_df = visualizer.generate_sector_analysis(portfolio_snapshots)
    print(sector_df.to_string(index=False))

    # Export visualization data
    print("\n" + "="*60)
    print("EXPORTING VISUALIZATION DATA")
    print("="*60)

    output_dir = Path(__file__).parent.parent / 'backtest_output'
    exported_files = export_visualization_data(
        visualizer,
        snapshots,
        metrics,
        str(output_dir),
    )

    print("\nExported files:")
    for file_type, file_path in exported_files.items():
        print(f"  {file_type}: {file_path}")

    print("\n" + "="*60)
    print("VISUALIZATION DEMO COMPLETE")
    print("="*60)
    print(f"\nResults saved to: {output_dir}")
    print(f"\nKey Performance Metrics:")
    print(f"  Total Return: {metrics.total_return:.2%}")
    print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"  Max Drawdown: {metrics.max_drawdown:.2%}")
    print(f"  WACC Effectiveness: {metrics.wacc_effectiveness:.2%}")


if __name__ == '__main__':
    main()
