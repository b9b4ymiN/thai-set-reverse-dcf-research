from __future__ import annotations

"""
Thai SET Backtest Engine

Unified backtest engine that integrates SignalGenerator, PortfolioConstructor,
and Rebalancer modules with comprehensive performance metrics calculation.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
import pandas as pd
import numpy as np

from .signal_generator import SignalGenerator, SignalScoringConfig, Signal
from .portfolio_constructor import (
    PortfolioConstructor,
    PortfolioConfig,
    Portfolio,
    Position,
)
from .rebalancer import (
    Rebalancer,
    RebalanceConfig,
    TransactionCostModel,
    RebalanceResult,
)


@dataclass
class BacktestConfig:
    """Configuration for the backtest engine."""

    # Data paths
    observations_path: str = 'research_data/latest/fundamental_observations.csv'
    price_history_path: str = 'research_data/latest/price_history.csv'
    benchmark_history_path: str = 'research_data/latest/benchmark_history.csv'
    snapshot_path: str = 'research_data/latest/fundamentals_snapshot.csv'

    # Backtest period
    start_date: str = '2020-01-01'
    end_date: str = '2025-12-31'
    rebalance_frequency: str = 'QE'  # Quarterly (using new pandas alias)

    # Portfolio settings
    max_positions: int = 20
    min_positions: int = 10
    position_sizing: str = 'equal_weight'  # equal_weight, signal_weighted, quality_weighted

    # Execution
    execution_delay_days: int = 1
    initial_capital: float = 1_000_000  # 1M THB

    # Signal generation
    default_wacc: float = 0.08
    top_n: int = 15

    # Cost model
    include_transaction_costs: bool = True


@dataclass
class EnginePerformanceMetrics:
    """Performance metrics for a backtest."""

    # Return metrics
    total_return: float
    annualized_return: float
    benchmark_return: float
    active_return: float

    # Risk metrics
    volatility: float
    benchmark_volatility: float
    tracking_error: float

    # Risk-adjusted metrics
    sharpe_ratio: float
    sortino_ratio: float
    information_ratio: float

    # Drawdown metrics
    max_drawdown: float
    max_drawdown_duration: int
    avg_drawdown: float

    # Trading metrics
    total_trades: int
    avg_turnover: float
    total_transaction_costs: float

    # Hit rate
    hit_rate: float
    win_count: int
    loss_count: int

    # Period breakdown
    num_periods: int
    profitable_periods: int


@dataclass
class BacktestResult:
    """Complete backtest results."""

    config: BacktestConfig
    metrics: EnginePerformanceMetrics
    equity_curve: pd.DataFrame
    portfolio_history: List[Portfolio]
    rebalance_history: List[RebalanceResult]
    signal_history: List[List[Signal]]
    trades: List

    def to_dataframe(self) -> pd.DataFrame:
        """Convert equity curve to DataFrame."""
        return self.equity_curve


class ThaiSETBacktestEngine:
    """
    Unified backtest engine for Thai SET reverse DCF strategy.

    Integrates signal generation, portfolio construction, and rebalancing
    with comprehensive performance metrics calculation.
    """

    def __init__(
        self,
        config: Optional[BacktestConfig] = None,
        signal_generator: Optional[SignalGenerator] = None,
        portfolio_constructor: Optional[PortfolioConstructor] = None,
        rebalancer: Optional[Rebalancer] = None,
    ):
        """
        Initialize backtest engine.

        Args:
            config: Backtest configuration
            signal_generator: Custom signal generator (optional)
            portfolio_constructor: Custom portfolio constructor (optional)
            rebalancer: Custom rebalancer (optional)
        """
        self.config = config or BacktestConfig()

        # Initialize components
        self.signal_generator = signal_generator or self._create_signal_generator()
        self.portfolio_constructor = portfolio_constructor or self._create_portfolio_constructor()
        self.rebalancer = rebalancer or self._create_rebalancer()

        # Load data
        self._load_data()

    def _create_signal_generator(self) -> SignalGenerator:
        """Create default signal generator."""
        config = SignalScoringConfig(
            use_sector_hurdle_rates=True,
            quality_over_quantity=True,
        )
        return SignalGenerator(config)

    def _create_portfolio_constructor(self) -> PortfolioConstructor:
        """Create default portfolio constructor."""
        from .portfolio_constructor import PositionSizingMethod

        sizing_method = {
            'equal_weight': PositionSizingMethod.EQUAL_WEIGHT,
            'signal_weighted': PositionSizingMethod.SIGNAL_WEIGHTED,
            'quality_weighted': PositionSizingMethod.QUALITY_WEIGHTED,
        }.get(self.config.position_sizing, PositionSizingMethod.EQUAL_WEIGHT)

        config = PortfolioConfig(
            max_positions=self.config.max_positions,
            min_positions=self.config.min_positions,
            sizing_method=sizing_method,
            quality_over_quantity=True,
        )
        return PortfolioConstructor(config)

    def _create_rebalancer(self) -> Rebalancer:
        """Create default rebalancer."""
        config = RebalanceConfig(
            rebalance_frequency_months=3,  # Quarterly
            execution_delay_days=self.config.execution_delay_days,
        )
        cost_model = TransactionCostModel() if self.config.include_transaction_costs else None
        return Rebalancer(config, cost_model)

    def _load_data(self):
        """Load all required data files."""
        self.observations = pd.read_csv(self.config.observations_path)
        self.prices = pd.read_csv(self.config.price_history_path)
        self.benchmark = pd.read_csv(self.config.benchmark_history_path)
        self.snapshot = pd.read_csv(self.config.snapshot_path)

        # Convert dates
        self.observations['Statement_Date'] = pd.to_datetime(self.observations['Statement_Date'])
        self.observations['Availability_Date'] = pd.to_datetime(self.observations['Availability_Date'])
        self.prices['Date'] = pd.to_datetime(self.prices['Date'])
        self.benchmark['Date'] = pd.to_datetime(self.benchmark['Date'])

        # Build lookups
        self.price_lookup = {
            ticker: frame.reset_index(drop=True)
            for ticker, frame in self.prices.groupby('Ticker', sort=False)
        }
        self.observation_lookup = {
            ticker: frame.reset_index(drop=True)
            for ticker, frame in self.observations.groupby('Ticker', sort=False)
        }
        self.snapshot_lookup = self.snapshot.set_index('Ticker').to_dict('index') if not self.snapshot.empty else {}

        # Get universe
        self.universe_tickers = sorted(set(self.observation_lookup) & set(self.price_lookup))

    def run(self) -> BacktestResult:
        """
        Run the complete backtest.

        Returns:
            BacktestResult with metrics and history
        """
        # Generate rebalance schedule
        rebalance_dates = self._build_rebalance_schedule()

        # Initialize state
        current_portfolio = None
        portfolio_history = []
        rebalance_history = []
        signal_history = []

        # Equity curve tracking
        equity_records = []
        current_capital = self.config.initial_capital

        # Trade tracking
        all_trades = []

        for rebalance_date in rebalance_dates:
            # Generate signals
            signals = self._generate_signals(rebalance_date)
            signal_history.append(signals)

            if not signals:
                continue

            # Construct target portfolio
            target_portfolio = self.portfolio_constructor.construct_portfolio(
                signals[:self.config.top_n],
                rebalance_date,
                current_portfolio,
            )

            # Get execution price data
            execution_date = rebalance_date + timedelta(days=self.config.execution_delay_days)
            price_data = self._get_price_data(execution_date)

            # Execute rebalance
            if current_portfolio is not None:
                rebalance_result = self.rebalancer.execute_rebalance(
                    current_portfolio,
                    target_portfolio,
                    execution_date,
                    price_data,
                )
                rebalance_history.append(rebalance_result)
                all_trades.extend(rebalance_result.trades)

                # Update capital (simplified - assumes mark-to-market)
                current_capital = self._calculate_portfolio_value(
                    current_portfolio, price_data
                )

            current_portfolio = target_portfolio
            portfolio_history.append(current_portfolio)

            # Calculate return for this period
            if len(portfolio_history) > 1:
                period_return = self._calculate_period_return(
                    portfolio_history[-2],
                    current_portfolio,
                    price_data,
                )

                # Benchmark return
                benchmark_return = self._calculate_benchmark_return(
                    rebalance_date - timedelta(days=90),  # Approximate
                    rebalance_date,
                )

                equity_records.append({
                    'Date': rebalance_date,
                    'Portfolio_Value': current_capital * (1 + period_return),
                    'Portfolio_Return': period_return,
                    'Benchmark_Return': benchmark_return,
                    'Active_Return': period_return - benchmark_return,
                    'Num_Positions': len(current_portfolio.positions),
                })

        # Build equity curve DataFrame
        equity_curve = pd.DataFrame(equity_records)

        # Calculate metrics
        metrics = self._calculate_metrics(equity_curve, rebalance_history)

        return BacktestResult(
            config=self.config,
            metrics=metrics,
            equity_curve=equity_curve,
            portfolio_history=portfolio_history,
            rebalance_history=rebalance_history,
            signal_history=signal_history,
            trades=all_trades,
        )

    def _build_rebalance_schedule(self) -> List[datetime]:
        """Build rebalance schedule."""
        start = pd.Timestamp(self.config.start_date)
        end = pd.Timestamp(self.config.end_date)

        # Get available price dates
        price_dates = pd.to_datetime(self.prices['Date'].dropna().unique())

        # Generate rebalance anchors
        anchors = pd.date_range(start=start, end=end, freq=self.config.rebalance_frequency)

        rebalance_dates = []
        for anchor in anchors:
            eligible = price_dates[price_dates >= anchor]
            if len(eligible) > 0:
                rebalance_dates.append(datetime.strptime(str(eligible[0].date()), '%Y-%m-%d'))

        return rebalance_dates

    def _generate_signals(self, rebalance_date: datetime) -> List[Signal]:
        """Generate signals for a given rebalance date."""
        rows = []

        # Build cross-section
        for ticker in self.universe_tickers:
            observation = self._latest_available_observation(ticker, rebalance_date)
            if observation is None:
                continue

            price_info = self._price_info_on_or_before(ticker, rebalance_date)
            if price_info is None:
                continue

            price, price_date = price_info
            if price <= 0:
                continue

            # Create row for signal generation
            row = self._create_signal_row(ticker, observation, price, price_date, rebalance_date)
            if row:
                rows.append(row)

        if not rows:
            return []

        # Generate signals using SignalGenerator
        cross_section = pd.DataFrame(rows)
        signals, _ = self.signal_generator.generate_signals(
            cross_section,
            rebalance_date,
            self.snapshot,
        )

        return signals

    def _latest_available_observation(self, ticker: str, rebalance_date: datetime) -> Optional[pd.Series]:
        """Get latest available observation before rebalance date."""
        frame = self.observation_lookup.get(ticker)
        if frame is None or frame.empty:
            return None

        eligible = frame.loc[frame['Availability_Date'] <= pd.Timestamp(rebalance_date)]
        if eligible.empty:
            return None

        eligible = eligible.sort_values(['Availability_Date', 'Statement_Date'])
        return eligible.iloc[-1]

    def _price_info_on_or_before(self, ticker: str, target_date: datetime) -> Optional[Tuple[float, datetime]]:
        """Get price info on or before target date."""
        frame = self.price_lookup.get(ticker)
        if frame is None or frame.empty:
            return None

        eligible = frame.loc[frame['Date'] <= pd.Timestamp(target_date)]
        if eligible.empty:
            return None

        row = eligible.iloc[-1]
        price = float(row['Adj Close'] if pd.notna(row['Adj Close']) else row['Close'])
        return price, pd.Timestamp(row['Date'])

    def _create_signal_row(
        self,
        ticker: str,
        observation: pd.Series,
        price: float,
        price_date: pd.Timestamp,
        rebalance_date: datetime,
    ) -> Optional[Dict]:
        """Create a row for signal generation."""
        from reverse_dcf_model import solve_reverse_dcf

        shares = observation.get('Diluted_Average_Shares') or observation.get('Shares_Issued')
        if pd.isna(shares) or shares <= 0:
            return None

        fcf = observation.get('FCF', 0)
        if pd.isna(fcf) or fcf <= 0:
            return None

        net_debt = observation.get('Net_Debt', 0) or 0

        # Solve reverse DCF
        implied_growth, details = solve_reverse_dcf(
            base_fcf=float(fcf),
            wacc=self.config.default_wacc,
            current_price=float(price),
            shares_outstanding=float(shares),
            net_debt=float(net_debt),
        )

        if not details.get('converged', True):
            return None

        actual_growth = observation.get('Revenue_Growth', 0)
        actual_growth = 0.0 if pd.isna(actual_growth) else float(actual_growth)
        signal_score = actual_growth - float(implied_growth)

        return {
            'Ticker': ticker,
            'Price': float(price),
            'FCF': float(fcf),
            'Shares': float(shares),
            'WACC': self.config.default_wacc,
            'Net_Debt': float(net_debt),
            'Actual_Revenue_Growth': actual_growth,
            'Implied_Growth_Rate': float(implied_growth),
            'Signal_Score': signal_score,
            'ROE': observation.get('ROE', 0),
            'Debt_to_Equity': observation.get('Debt_to_Equity', 0),
            'PE_Ratio': observation.get('PE_Ratio', None),
            'PB_Ratio': observation.get('PB_Ratio', None),
            'Market_Cap': observation.get('Market_Cap', 0),
            'No_Lookahead_Pass': (
                pd.Timestamp(observation['Availability_Date']) <= pd.Timestamp(rebalance_date) and
                price_date <= pd.Timestamp(rebalance_date)
            ),
        }

    def _get_price_data(self, date: datetime) -> Dict[str, float]:
        """Get price data for all tickers on a given date."""
        price_data = {}
        for ticker in self.universe_tickers:
            info = self._price_info_on_or_before(ticker, date)
            if info:
                price_data[ticker] = info[0]
        return price_data

    def _calculate_portfolio_value(
        self,
        portfolio: Portfolio,
        price_data: Dict[str, float],
    ) -> float:
        """Calculate current portfolio value."""
        total_value = 0.0
        for position in portfolio.positions:
            price = price_data.get(position.ticker, position.entry_price)
            total_value += position.weight * price

        return total_value if total_value > 0 else self.config.initial_capital

    def _calculate_period_return(
        self,
        old_portfolio: Portfolio,
        new_portfolio: Portfolio,
        price_data: Dict[str, float],
    ) -> float:
        """Calculate return for a period."""
        # Simplified return calculation
        old_value = self._calculate_portfolio_value(old_portfolio, price_data)
        new_value = self._calculate_portfolio_value(new_portfolio, price_data)

        if old_value == 0:
            return 0.0

        return (new_value - old_value) / old_value

    def _calculate_benchmark_return(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate benchmark return for period."""
        start_price = self._series_price_on_or_before(self.benchmark, start_date)
        end_price = self._series_price_on_or_before(self.benchmark, end_date)

        if start_price is None or end_price is None or start_price <= 0:
            return 0.0

        return (end_price / start_price) - 1

    @staticmethod
    def _series_price_on_or_before(frame: pd.DataFrame, target_date: datetime) -> Optional[float]:
        """Get price from series on or before date."""
        eligible = frame.loc[frame['Date'] <= pd.Timestamp(target_date)]
        if eligible.empty:
            return None
        row = eligible.iloc[-1]
        return float(row['Adj Close'] if pd.notna(row['Adj Close']) else row['Close'])

    def _calculate_metrics(
        self,
        equity_curve: pd.DataFrame,
        rebalance_history: List[RebalanceResult],
    ) -> EnginePerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        if equity_curve.empty:
            return self._empty_metrics()

        returns = equity_curve['Portfolio_Return'].values
        benchmark_returns = equity_curve['Benchmark_Return'].values
        active_returns = equity_curve['Active_Return'].values

        # Return metrics
        total_return = equity_curve['Portfolio_Return'].sum()
        annualized_return = self._annualize_return(total_return, len(returns))
        benchmark_total = equity_curve['Benchmark_Return'].sum()
        active_total = total_return - benchmark_total

        # Risk metrics
        volatility = np.std(returns) * np.sqrt(4)  # Quarterly to annual
        benchmark_volatility = np.std(benchmark_returns) * np.sqrt(4)
        tracking_error = np.std(active_returns) * np.sqrt(4)

        # Risk-adjusted metrics
        sharpe = self._calculate_sharpe(returns, volatility)
        sortino = self._calculate_sortino(returns)
        information_ratio = self._calculate_information_ratio(active_returns, tracking_error)

        # Drawdown metrics
        equity_values = equity_curve['Portfolio_Value'].values
        max_dd, max_dd_dur, avg_dd = self._calculate_drawdowns(equity_values)

        # Trading metrics
        total_trades = sum(len(r.trades) for r in rebalance_history)
        avg_turnover = np.mean([r.turnover_rate for r in rebalance_history]) if rebalance_history else 0
        total_costs = sum(r.total_transaction_cost for r in rebalance_history)

        # Hit rate
        hit_rate = np.mean(active_returns > 0) * 100
        win_count = np.sum(active_returns > 0)
        loss_count = np.sum(active_returns <= 0)

        return EnginePerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            benchmark_return=benchmark_total,
            active_return=active_total,
            volatility=volatility,
            benchmark_volatility=benchmark_volatility,
            tracking_error=tracking_error,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            information_ratio=information_ratio,
            max_drawdown=max_dd,
            max_drawdown_duration=max_dd_dur,
            avg_drawdown=avg_dd,
            total_trades=total_trades,
            avg_turnover=avg_turnover,
            total_transaction_costs=total_costs,
            hit_rate=hit_rate,
            win_count=int(win_count),
            loss_count=int(loss_count),
            num_periods=len(returns),
            profitable_periods=int(win_count),
        )

    def _empty_metrics(self) -> EnginePerformanceMetrics:
        """Return empty metrics."""
        return EnginePerformanceMetrics(
            total_return=0.0,
            annualized_return=0.0,
            benchmark_return=0.0,
            active_return=0.0,
            volatility=0.0,
            benchmark_volatility=0.0,
            tracking_error=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            information_ratio=0.0,
            max_drawdown=0.0,
            max_drawdown_duration=0,
            avg_drawdown=0.0,
            total_trades=0,
            avg_turnover=0.0,
            total_transaction_costs=0.0,
            hit_rate=0.0,
            win_count=0,
            loss_count=0,
            num_periods=0,
            profitable_periods=0,
        )

    def _annualize_return(self, total_return: float, num_periods: int) -> float:
        """Annualize return."""
        if num_periods == 0:
            return 0.0
        years = num_periods / 4  # Quarterly periods
        return (1 + total_return) ** (1 / years) - 1

    def _calculate_sharpe(self, returns: np.ndarray, volatility: float) -> float:
        """Calculate Sharpe ratio."""
        if volatility == 0:
            return 0.0
        risk_free_rate = 0.02  # 2% annual risk-free rate
        excess_return = np.mean(returns) * 4 - risk_free_rate  # Quarterly to annual
        return excess_return / volatility

    def _calculate_sortino(self, returns: np.ndarray) -> float:
        """Calculate Sortino ratio."""
        mean_return = np.mean(returns) * 4
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float('inf') if mean_return > 0 else 0.0

        downside_deviation = np.std(downside_returns) * np.sqrt(4)
        if downside_deviation == 0:
            return 0.0

        risk_free_rate = 0.02
        excess_return = mean_return - risk_free_rate
        return excess_return / downside_deviation

    def _calculate_information_ratio(
        self,
        active_returns: np.ndarray,
        tracking_error: float,
    ) -> float:
        """Calculate Information Ratio."""
        if tracking_error == 0:
            return 0.0
        return np.mean(active_returns) * 4 / tracking_error

    def _calculate_drawdowns(self, equity_values: np.ndarray) -> Tuple[float, int, float]:
        """Calculate drawdown metrics."""
        if len(equity_values) == 0:
            return 0.0, 0, 0.0

        # Calculate running maximum
        running_max = np.maximum.accumulate(equity_values)

        # Calculate drawdowns
        drawdowns = (equity_values - running_max) / running_max

        max_dd = float(np.min(drawdowns))
        avg_dd = float(np.mean(drawdowns))

        # Find max drawdown duration
        max_dd_dur = 0
        current_dur = 0

        for dd in drawdowns:
            if dd < 0:
                current_dur += 1
                max_dd_dur = max(max_dd_dur, current_dur)
            else:
                current_dur = 0

        return max_dd, max_dd_dur, avg_dd
