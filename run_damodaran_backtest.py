#!/usr/bin/env python3
"""
Run Reverse DCF Backtest with Damodaran-style dynamic WACC.
"""

import os
from pathlib import Path
from src.pipeline.backtest import ReverseDCFBacktester, DEFAULT_HORIZONS

def run_damodaran_backtest():
    output_dir = Path('research_data/source_of_truth_100/backtest_damodaran')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("🚀 Starting Damodaran-style Backtest...")
    
    backtester = ReverseDCFBacktester(
        snapshot_path='research_data/source_of_truth_100/fundamentals_snapshot.csv',
        observations_path='research_data/source_of_truth_100/fundamental_observations.csv',
        price_history_path='research_data/source_of_truth_100/price_history.csv',
        benchmark_history_path='research_data/source_of_truth_100/benchmark_history.csv',
        wacc_mode='damodaran'
    )

    result = backtester.run(
        output_dir=str(output_dir),
        horizons=DEFAULT_HORIZONS,
        top_n=10,
        rebalance_frequency='Q',
        start_date='2020-01-01',
        case_name='damodaran'
    )

    print("\n✅ Backtest Complete!")
    print(f"📊 Signals generated: {result['signals']}")
    print(f"📂 Results saved to: {output_dir}")
    
    # Print summary
    import pandas as pd
    summary = pd.read_csv(output_dir / 'summary.csv')
    print("\nSummary Results:")
    print(summary[['Horizon_Months', 'Portfolio_Return', 'Benchmark_Return', 'Active_Return', 'Hit_Rate']].to_string(index=False))

if __name__ == "__main__":
    run_damodaran_backtest()
