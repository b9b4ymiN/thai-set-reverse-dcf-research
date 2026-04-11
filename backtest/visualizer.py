"""
Visualization Module for Reverse DCF Backtest Engine

Provides comprehensive visualization capabilities for backtest results,
portfolio performance, and signal analysis following Damodaran's principles.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np


@dataclass
class VisualizationConfig:
    """Configuration for visualization outputs."""

    # Plot settings
    figsize: Tuple[int, int] = (12, 8)
    dpi: int = 100
    style: str = 'seaborn-v0_8-darkgrid'

    # Color schemes
    color_portfolio: str = '#2E86AB'
    color_benchmark: str = '#A23B72'
    color_positive: str = '#06A77D'
    color_negative: str = '#D62246'

    # Display settings
    show_benchmark: bool = True
    show_drawdown: bool = True
    show_attribution: bool = True

    # Attribution settings (Damodaran principles)
    use_fixed_wacc: bool = True
    fixed_wacc: float = 0.08  # 8% fixed WACC for Thailand
    sector_adjustments: bool = True

    # Performance metrics
    risk_free_rate: float = 0.03  # 3% risk-free rate


@dataclass
class BacktestSnapshot:
    """Single period snapshot of backtest results."""

    date: datetime
    portfolio_value: float
    benchmark_value: float
    returns: float
    benchmark_returns: float
    positions_held: int
    cash: float

    # Attribution components
    stock_selection_return: float = 0.0
    sector_allocation_return: float = 0.0
    timing_return: float = 0.0

    # Risk metrics
    portfolio_volatility: float = 0.0
    max_drawdown: float = 0.0


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for backtest."""

    # Return metrics
    total_return: float
    annualized_return: float
    cagr: float

    # Risk metrics
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float

    # Attribution metrics (Damodaran principles)
    avg_growth_differential: float
    wacc_effectiveness: float
    sector_adjustment_impact: float

    # Trading metrics
    total_trades: int
    turnover_rate: float
    avg_hold_period: float


class BacktestVisualizer:
    """
    Visualize backtest results with attribution analysis.

    Follows Damodaran's time-varying principles with fixed WACC methodology.
    """

    def __init__(self, config: Optional[VisualizationConfig] = None):
        """Initialize visualizer with configuration."""
        self.config = config or VisualizationConfig()

    def prepare_backtest_data(
        self,
        price_history: pd.DataFrame,
        benchmark_history: pd.DataFrame,
        portfolio_snapshots: List[Dict],
        rebalance_dates: List[datetime],
    ) -> Tuple[List[BacktestSnapshot], PerformanceMetrics]:
        """
        Prepare backtest data for visualization.

        Args:
            price_history: DataFrame with price data (tickers as columns)
            benchmark_history: DataFrame with benchmark index values
            portfolio_snapshots: List of portfolio state dictionaries
            rebalance_dates: Dates when portfolio was rebalanced

        Returns:
            Tuple of (snapshots, performance metrics)
        """
        snapshots = []

        for i, snapshot in enumerate(portfolio_snapshots):
            date = snapshot.get('date')

            # Calculate returns
            portfolio_value = snapshot.get('total_value', 0)
            benchmark_value = benchmark_history.loc[date].iloc[0] if date in benchmark_history.index else 1000

            prev_portfolio = portfolio_snapshots[i-1].get('total_value', portfolio_value) if i > 0 else portfolio_value
            prev_benchmark = benchmark_history.loc[rebalance_dates[i-1]].iloc[0] if i > 0 and rebalance_dates[i-1] in benchmark_history.index else benchmark_value

            returns = (portfolio_value - prev_portfolio) / prev_portfolio if prev_portfolio > 0 else 0
            benchmark_returns = (benchmark_value - prev_benchmark) / prev_benchmark if prev_benchmark > 0 else 0

            # Calculate attribution components
            stock_selection = self._calculate_stock_selection_attribution(snapshot)
            sector_allocation = self._calculate_sector_allocation_attribution(snapshot)
            timing = returns - stock_selection - sector_allocation

            snap = BacktestSnapshot(
                date=date,
                portfolio_value=portfolio_value,
                benchmark_value=benchmark_value,
                returns=returns,
                benchmark_returns=benchmark_returns,
                positions_held=len(snapshot.get('positions', [])),
                cash=snapshot.get('cash', 0),
                stock_selection_return=stock_selection,
                sector_allocation_return=sector_allocation,
                timing_return=timing,
                portfolio_volatility=snapshot.get('volatility', 0),
                max_drawdown=snapshot.get('drawdown', 0),
            )
            snapshots.append(snap)

        # Calculate aggregate metrics
        metrics = self._calculate_performance_metrics(snapshots)

        return snapshots, metrics

    def _calculate_stock_selection_attribution(self, snapshot: Dict) -> float:
        """Calculate stock selection attribution."""
        positions = snapshot.get('positions', [])
        if not positions:
            return 0.0

        # Weighted average of individual stock returns
        total_weight = sum(p.get('weight', 0) for p in positions)
        if total_weight == 0:
            return 0.0

        weighted_return = sum(
            p.get('weight', 0) * p.get('return', 0)
            for p in positions
        )

        return weighted_return / total_weight

    def _calculate_sector_allocation_attribution(self, snapshot: Dict) -> float:
        """Calculate sector allocation attribution (Damodaran principle)."""
        positions = snapshot.get('positions', [])
        if not positions:
            return 0.0

        # Group by sector
        sector_returns = {}
        sector_weights = {}

        for pos in positions:
            sector = pos.get('sector', 'Unknown')
            sector_returns[sector] = sector_returns.get(sector, 0) + pos.get('return', 0)
            sector_weights[sector] = sector_weights.get(sector, 0) + pos.get('weight', 0)

        # Calculate allocation effect
        allocation_effect = 0.0
        for sector, weight in sector_weights.items():
            sector_return = sector_returns.get(sector, 0) / sum(
                p.get('weight', 0) for p in positions if p.get('sector') == sector
            ) if any(p.get('sector') == sector for p in positions) else 0
            allocation_effect += weight * sector_return

        return allocation_effect

    def _calculate_performance_metrics(
        self,
        snapshots: List[BacktestSnapshot],
    ) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        if not snapshots:
            return PerformanceMetrics(
                total_return=0, annualized_return=0, cagr=0,
                volatility=0, sharpe_ratio=0, sortino_ratio=0,
                max_drawdown=0, calmar_ratio=0,
                avg_growth_differential=0, wacc_effectiveness=0,
                sector_adjustment_impact=0, total_trades=0,
                turnover_rate=0, avg_hold_period=0,
            )

        # Extract returns
        returns = [s.returns for s in snapshots]
        benchmark_returns = [s.benchmark_returns for s in snapshots]

        # Return metrics
        total_return = (snapshots[-1].portfolio_value / snapshots[0].portfolio_value) - 1
        n_periods = len(snapshots)
        annualized_return = np.mean(returns) * 4 if n_periods > 0 else 0  # Quarterly
        cagr = (snapshots[-1].portfolio_value / snapshots[0].portfolio_value) ** (1 / (n_periods / 4)) - 1 if n_periods > 0 else 0

        # Risk metrics
        volatility = np.std(returns) * 2 if len(returns) > 1 else 0  # Annualized
        excess_returns = [r - self.config.risk_free_rate / 4 for r in returns]
        sharpe_ratio = np.mean(excess_returns) / (np.std(excess_returns) * 2) if len(excess_returns) > 1 else 0

        # Sortino ratio (downside risk)
        downside_returns = [r for r in returns if r < 0]
        downside_deviation = np.std(downside_returns) * 2 if downside_returns else 0
        sortino_ratio = annualized_return / downside_deviation if downside_deviation > 0 else 0

        # Drawdown metrics
        max_drawdown = max(s.max_drawdown for s in snapshots)
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Attribution metrics (Damodaran)
        avg_growth_diff = np.mean([
            s.stock_selection_return for s in snapshots
        ]) if snapshots else 0

        wacc_effectiveness = self._calculate_wacc_effectiveness(snapshots)
        sector_impact = np.mean([s.sector_allocation_return for s in snapshots])

        # Trading metrics
        total_trades = sum(
            s.positions_held for s in snapshots
        )  # Simplified

        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            cagr=cagr,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            avg_growth_differential=avg_growth_diff,
            wacc_effectiveness=wacc_effectiveness,
            sector_adjustment_impact=sector_impact,
            total_trades=total_trades,
            turnover_rate=0.2,  # Placeholder
            avg_hold_period=90,  # Placeholder (days)
        )

    def _calculate_wacc_effectiveness(
        self,
        snapshots: List[BacktestSnapshot],
    ) -> float:
        """
        Calculate WACC effectiveness (Damodaran principle).

        Measures how well fixed WACC methodology performed relative to
        time-varying WACC scenarios.
        """
        # Simplified: compare portfolio return to benchmark
        if len(snapshots) < 2:
            return 0.0

        portfolio_return = (snapshots[-1].portfolio_value / snapshots[0].portfolio_value) - 1
        benchmark_return = (snapshots[-1].benchmark_value / snapshots[0].benchmark_value) - 1

        # Effectiveness = excess return attributable to WACC methodology
        effectiveness = portfolio_return - benchmark_return

        return effectiveness

    def generate_summary_table(
        self,
        metrics: PerformanceMetrics,
        snapshots: List[BacktestSnapshot],
    ) -> pd.DataFrame:
        """
        Generate summary table of backtest results.

        Returns DataFrame with key metrics formatted for display.
        """
        summary_data = {
            'Metric': [
                'Total Return',
                'Annualized Return',
                'CAGR',
                'Volatility',
                'Sharpe Ratio',
                'Sortino Ratio',
                'Max Drawdown',
                'Calmar Ratio',
                'Avg Growth Differential',
                'WACC Effectiveness',
                'Sector Adjustment Impact',
                'Total Trades',
                'Turnover Rate',
                'Avg Hold Period (days)',
            ],
            'Value': [
                f"{metrics.total_return:.2%}",
                f"{metrics.annualized_return:.2%}",
                f"{metrics.cagr:.2%}",
                f"{metrics.volatility:.2%}",
                f"{metrics.sharpe_ratio:.2f}",
                f"{metrics.sortino_ratio:.2f}",
                f"{metrics.max_drawdown:.2%}",
                f"{metrics.calmar_ratio:.2f}",
                f"{metrics.avg_growth_differential:.4f}",
                f"{metrics.wacc_effectiveness:.2%}",
                f"{metrics.sector_adjustment_impact:.2%}",
                metrics.total_trades,
                f"{metrics.turnover_rate:.2%}",
                f"{metrics.avg_hold_period:.0f}",
            ],
        }

        return pd.DataFrame(summary_data)

    def prepare_time_series_data(
        self,
        snapshots: List[BacktestSnapshot],
    ) -> pd.DataFrame:
        """
        Prepare time series data for visualization.

        Returns DataFrame with date, portfolio value, benchmark value,
        and returns for each period.
        """
        data = {
            'Date': [s.date for s in snapshots],
            'Portfolio_Value': [s.portfolio_value for s in snapshots],
            'Benchmark_Value': [s.benchmark_value for s in snapshots],
            'Returns': [s.returns for s in snapshots],
            'Benchmark_Returns': [s.benchmark_returns for s in snapshots],
            'Positions_Held': [s.positions_held for s in snapshots],
            'Cash': [s.cash for s in snapshots],
            'Drawdown': [s.max_drawdown for s in snapshots],
            'Stock_Selection': [s.stock_selection_return for s in snapshots],
            'Sector_Allocation': [s.sector_allocation_return for s in snapshots],
            'Timing': [s.timing_return for s in snapshots],
        }

        df = pd.DataFrame(data)
        df.set_index('Date', inplace=True)

        return df

    def prepare_attribution_analysis(
        self,
        snapshots: List[BacktestSnapshot],
    ) -> pd.DataFrame:
        """
        Prepare attribution analysis data.

        Returns DataFrame with cumulative attribution effects over time.
        """
        attribution_data = {
            'Date': [s.date for s in snapshots],
            'Stock_Selection': [s.stock_selection_return for s in snapshots],
            'Sector_Allocation': [s.sector_allocation_return for s in snapshots],
            'Timing': [s.timing_return for s in snapshots],
            'Total_Attribution': [
                s.stock_selection_return + s.sector_allocation_return + s.timing_return
                for s in snapshots
            ],
        }

        df = pd.DataFrame(attribution_data)
        df.set_index('Date', inplace=True)

        # Calculate cumulative attribution
        df['Cumulative_Stock_Selection'] = df['Stock_Selection'].cumsum()
        df['Cumulative_Sector_Allocation'] = df['Sector_Allocation'].cumsum()
        df['Cumulative_Timing'] = df['Timing'].cumsum()
        df['Cumulative_Total'] = df['Total_Attribution'].cumsum()

        return df

    def generate_sector_analysis(
        self,
        portfolio_snapshots: List[Dict],
    ) -> pd.DataFrame:
        """
        Generate sector-wise performance analysis.

        Returns DataFrame with sector weights, returns, and attribution.
        """
        sector_data = {}

        for snapshot in portfolio_snapshots:
            positions = snapshot.get('positions', [])

            for pos in positions:
                sector = pos.get('sector', 'Unknown')

                if sector not in sector_data:
                    sector_data[sector] = {
                        'total_weight': 0,
                        'total_return': 0,
                        'count': 0,
                    }

                sector_data[sector]['total_weight'] += pos.get('weight', 0)
                sector_data[sector]['total_return'] += pos.get('return', 0)
                sector_data[sector]['count'] += 1

        # Calculate averages
        sector_summary = []
        for sector, data in sector_data.items():
            avg_return = data['total_return'] / data['count'] if data['count'] > 0 else 0
            sector_summary.append({
                'Sector': sector,
                'Avg_Weight': data['total_weight'] / len(portfolio_snapshots),
                'Avg_Return': avg_return,
                'Num_Positions': data['count'],
            })

        return pd.DataFrame(sector_summary).sort_values('Avg_Return', ascending=False)


def export_visualization_data(
    visualizer: BacktestVisualizer,
    snapshots: List[BacktestSnapshot],
    metrics: PerformanceMetrics,
    output_dir: str,
) -> Dict[str, str]:
    """
    Export visualization data to CSV files.

    Args:
        visualizer: BacktestVisualizer instance
        snapshots: List of backtest snapshots
        metrics: Performance metrics
        output_dir: Directory to save files

    Returns:
        Dict mapping file type to file path
    """
    from pathlib import Path

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    exported_files = {}

    # Export summary table
    summary_df = visualizer.generate_summary_table(metrics, snapshots)
    summary_path = output_path / 'backtest_summary.csv'
    summary_df.to_csv(summary_path, index=False)
    exported_files['summary'] = str(summary_path)

    # Export time series
    ts_df = visualizer.prepare_time_series_data(snapshots)
    ts_path = output_path / 'time_series.csv'
    ts_df.to_csv(ts_path)
    exported_files['time_series'] = str(ts_path)

    # Export attribution
    attr_df = visualizer.prepare_attribution_analysis(snapshots)
    attr_path = output_path / 'attribution.csv'
    attr_df.to_csv(attr_path)
    exported_files['attribution'] = str(attr_path)

    return exported_files
