"""
Rebalancer for Reverse DCF Backtest

Handles portfolio rebalancing logic with transaction costs and execution rules.
Implements quarterly rebalancing with entry/exit rules and cost assumptions.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from .portfolio_constructor import Portfolio, Position, PortfolioConfig


@dataclass
class TransactionCostModel:
    """Transaction cost assumptions for Thai SET market."""

    # Trading costs
    commission_rate: float = 0.00015  # 0.015% commission (typical for Thai brokers)
    vat_rate: float = 0.07  # 7% VAT on commission
    settlement_fee_rate: float = 0.0001  # 0.01% SET settlement fee

    # Market impact (slippage)
    buy_slippage: float = 0.001  # 0.1% buy-side slippage
    sell_slippage: float = 0.001  # 0.1% sell-side slippage

    # Taxes
    withholding_tax_rate: float = 0.10  # 10% withholding on dividends

    # Stamp duty
    stamp_duty_rate: float = 0.001  # 0.1% stamp duty on buy trades only

    def calculate_buy_cost(self, notional: float) -> float:
        """Calculate total transaction cost for buy order."""
        # Commission
        commission = notional * self.commission_rate
        vat = commission * self.vat_rate
        settlement_fee = notional * self.settlement_fee_rate
        stamp_duty = notional * self.stamp_duty_rate

        # Slippage
        slippage = notional * self.buy_slippage

        total_cost = commission + vat + settlement_fee + stamp_duty + slippage
        return total_cost

    def calculate_sell_cost(self, notional: float) -> float:
        """Calculate total transaction cost for sell order."""
        # Commission
        commission = notional * self.commission_rate
        vat = commission * self.vat_rate
        settlement_fee = notional * self.settlement_fee_rate

        # Slippage
        slippage = notional * self.sell_slippage

        # No stamp duty on sell
        total_cost = commission + vat + settlement_fee + slippage
        return total_cost

    def total_round_trip_cost(self, notional: float) -> float:
        """Calculate total cost for buy + sell round trip."""
        return self.calculate_buy_cost(notional) + self.calculate_sell_cost(notional)


@dataclass
class RebalanceConfig:
    """Configuration for rebalancing rules."""

    # Frequency
    rebalance_frequency_months: int = 3  # Quarterly rebalancing
    minimum_hold_period_months: int = 1  # Minimum 1 month hold

    # Entry/Exit rules
    min_signal_score: float = 0.0  # Minimum signal score to enter
    max_signal_score_decline: float = 0.5  # Exit if signal declines by 50%
    stop_loss_pct: float = -0.25  # Exit if position down 25%

    # Portfolio rules
    min_portfolio_size: int = 10
    max_portfolio_size: int = 25
    target_portfolio_size: int = 15

    # Execution
    use_limit_orders: bool = True
    execution_delay_days: int = 1  # 1 trading day execution delay
    partial_fill_allowed: bool = True


@dataclass
class Trade:
    """Single trade execution."""

    ticker: str
    action: str  # 'buy' or 'sell'
    shares: int
    price: float
    notional: float
    transaction_cost: float
    execution_date: datetime
    signal_score: float
    reason: str  # 'entry', 'exit', 'rebalance', 'stop_loss'


@dataclass
class RebalanceResult:
    """Result of rebalancing operation."""

    previous_portfolio: Portfolio
    new_portfolio: Portfolio
    trades: List[Trade]
    total_transaction_cost: float
    turnover_rate: float
    rebalance_date: datetime
    execution_summary: Dict[str, any]


class Rebalancer:
    """
    Manage portfolio rebalancing with transaction costs and execution rules.

    Implements quarterly rebalancing with entry/exit rules following
    Damodaran's principles of minimizing turnover and transaction costs.
    """

    def __init__(
        self,
        config: Optional[RebalanceConfig] = None,
        cost_model: Optional[TransactionCostModel] = None,
    ):
        """Initialize rebalancer with configuration and cost model."""
        self.config = config or RebalanceConfig()
        self.cost_model = cost_model or TransactionCostModel()

    def should_rebalance(
        self,
        last_rebalance_date: datetime,
        current_date: datetime,
    ) -> bool:
        """
        Check if rebalancing is due based on frequency.

        Args:
            last_rebalance_date: Date of last rebalance
            current_date: Current evaluation date

        Returns:
            True if rebalancing is due
        """
        months_since_rebalance = (
            current_date.year - last_rebalance_date.year
        ) * 12 + current_date.month - last_rebalance_date.month

        return months_since_rebalance >= self.config.rebalance_frequency_months

    def generate_rebalance_trades(
        self,
        current_portfolio: Portfolio,
        target_portfolio: Portfolio,
        execution_date: datetime,
        price_data: Dict[str, float],
    ) -> List[Trade]:
        """
        Generate list of trades to transition from current to target portfolio.

        Args:
            current_portfolio: Existing portfolio positions
            target_portfolio: Desired portfolio positions
            execution_date: Date to execute trades
            price_data: Dictionary of current prices by ticker

        Returns:
            List of Trade objects
        """
        trades = []
        current_positions = {p.ticker: p for p in current_portfolio.positions}
        target_positions = {p.ticker: p for p in target_portfolio.positions}

        # Sell positions not in target
        for ticker, position in current_positions.items():
            if ticker not in target_positions:
                price = price_data.get(ticker, position.entry_price)
                notional = position.shares * price
                cost = self.cost_model.calculate_sell_cost(notional)

                trade = Trade(
                    ticker=ticker,
                    action='sell',
                    shares=position.shares,
                    price=price,
                    notional=notional,
                    transaction_cost=cost,
                    execution_date=execution_date,
                    signal_score=position.signal_score,
                    reason='exit',
                )
                trades.append(trade)

        # Buy new positions or adjust existing
        for ticker, target_pos in target_positions.items():
            price = price_data.get(ticker, target_pos.entry_price)
            current_pos = current_positions.get(ticker)

            if current_pos is None:
                # New position - buy full amount
                notional = target_pos.notional
                cost = self.cost_model.calculate_buy_cost(notional)

                trade = Trade(
                    ticker=ticker,
                    action='buy',
                    shares=target_pos.shares,
                    price=price,
                    notional=notional,
                    transaction_cost=cost,
                    execution_date=execution_date,
                    signal_score=target_pos.signal_score,
                    reason='entry',
                )
                trades.append(trade)
            else:
                # Adjust existing position
                shares_diff = target_pos.shares - current_pos.shares

                if abs(shares_diff) > 0:
                    action = 'buy' if shares_diff > 0 else 'sell'
                    notional = abs(shares_diff) * price

                    if action == 'buy':
                        cost = self.cost_model.calculate_buy_cost(notional)
                    else:
                        cost = self.cost_model.calculate_sell_cost(notional)

                    trade = Trade(
                        ticker=ticker,
                        action=action,
                        shares=abs(shares_diff),
                        price=price,
                        notional=notional,
                        transaction_cost=cost,
                        execution_date=execution_date,
                        signal_score=target_pos.signal_score,
                        reason='rebalance',
                    )
                    trades.append(trade)

        return trades

    def check_exit_triggers(
        self,
        portfolio: Portfolio,
        current_prices: Dict[str, float],
        current_date: datetime,
        purchase_dates: Dict[str, datetime],
    ) -> List[str]:
        """
        Check if any positions hit exit triggers (stop loss, signal decline).

        Returns list of tickers to exit.
        """
        exit_tickers = []

        for position in portfolio.positions:
            ticker = position.ticker
            current_price = current_prices.get(ticker)

            if current_price is None:
                continue

            # Check stop loss
            price_change_pct = (current_price / position.entry_price) - 1
            if price_change_pct <= self.config.stop_loss_pct:
                exit_tickers.append(ticker)
                continue

            # Check minimum hold period
            if ticker in purchase_dates:
                hold_duration = current_date - purchase_dates[ticker]
                min_hold = timedelta(days=self.config.minimum_hold_period_months * 30)
                if hold_duration < min_hold:
                    continue

            # Check signal score decline (if signal data available)
            # This would require access to current signal scores
            # For now, skip this check

        return exit_tickers

    def execute_rebalance(
        self,
        current_portfolio: Portfolio,
        target_portfolio: Portfolio,
        execution_date: datetime,
        price_data: Dict[str, float],
    ) -> RebalanceResult:
        """
        Execute rebalance from current to target portfolio.

        Args:
            current_portfolio: Existing portfolio
            target_portfolio: Desired portfolio
            execution_date: Execution date
            price_data: Current prices by ticker

        Returns:
            RebalanceResult with trades and summary
        """
        # Generate trades
        trades = self.generate_rebalance_trades(
            current_portfolio,
            target_portfolio,
            execution_date,
            price_data,
        )

        # Calculate total costs
        total_cost = sum(t.transaction_cost for t in trades)

        # Calculate turnover
        current_tickers = {p.ticker for p in current_portfolio.positions}
        target_tickers = {p.ticker for p in target_portfolio.positions}

        added = target_tickers - current_tickers
        removed = current_tickers - target_tickers

        turnover = (
            len(added) + len(removed)
        ) / max(len(current_tickers), 1)

        # Execution summary
        summary = {
            'total_trades': len(trades),
            'buy_trades': len([t for t in trades if t.action == 'buy']),
            'sell_trades': len([t for t in trades if t.action == 'sell']),
            'total_notional': sum(t.notional for t in trades),
            'total_cost_bps': (total_cost / sum(t.notional for t in trades) * 10000) if trades else 0,
            'positions_added': len(added),
            'positions_removed': len(removed),
            'positions_retained': len(current_tickers & target_tickers),
        }

        return RebalanceResult(
            previous_portfolio=current_portfolio,
            new_portfolio=target_portfolio,
            trades=trades,
            total_transaction_cost=total_cost,
            turnover_rate=turnover,
            rebalance_date=execution_date,
            execution_summary=summary,
        )

    def calculate_rebalance_schedule(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[datetime]:
        """
        Generate list of rebalance dates.

        Args:
            start_date: Backtest start date
            end_date: Backtest end date

        Returns:
            List of rebalance dates
        """
        dates = []
        current = start_date

        while current <= end_date:
            dates.append(current)
            # Add months for next rebalance
            current = current + timedelta(days=31 * self.config.rebalance_frequency_months)

        return dates

    def estimate_annual_transaction_costs(
        self,
        portfolio: Portfolio,
        expected_turnover: float,
        avg_notional_per_trade: float = 100_000,
    ) -> float:
        """
        Estimate annual transaction costs for a portfolio.

        Args:
            portfolio: Portfolio to estimate for
            expected_turnover: Expected annual turnover rate
            avg_notional_per_trade: Average notional value per trade

        Returns:
            Estimated annual transaction costs as percentage of portfolio value
        """
        # Number of rebalances per year
        rebalances_per_year = 12 / self.config.rebalance_frequency_months

        # Average trades per rebalance
        avg_positions = len(portfolio.positions)
        trades_per_rebalance = int(avg_positions * expected_turnover)

        # Cost per trade (average of buy and sell)
        avg_cost_per_trade = (
            self.cost_model.calculate_buy_cost(avg_notional_per_trade) +
            self.cost_model.calculate_sell_cost(avg_notional_per_trade)
        ) / 2

        # Annual cost
        annual_cost = rebalances_per_year * trades_per_rebalance * avg_cost_per_trade

        # As percentage of portfolio
        portfolio_value = avg_positions * avg_notional_per_trade
        cost_percentage = annual_cost / portfolio_value if portfolio_value > 0 else 0

        return cost_percentage

    def get_rebalance_summary(self, result: RebalanceResult) -> Dict[str, any]:
        """
        Generate summary statistics for rebalance result.

        Returns dict with key metrics and trade breakdown.
        """
        buy_trades = [t for t in result.trades if t.action == 'buy']
        sell_trades = [t for t in result.trades if t.action == 'sell']

        return {
            'rebalance_date': result.rebalance_date.isoformat(),
            'turnover_rate': result.turnover_rate,
            'total_transaction_cost': result.total_transaction_cost,
            'total_trades': len(result.trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_buy_notional': sum(t.notional for t in buy_trades),
            'total_sell_notional': sum(t.notional for t in sell_trades),
            'cost_bps': result.execution_summary.get('total_cost_bps', 0),
            'positions_before': len(result.previous_portfolio.positions),
            'positions_after': len(result.new_portfolio.positions),
            'top_buy_trades': [
                {
                    'ticker': t.ticker,
                    'notional': t.notional,
                    'cost': t.transaction_cost,
                }
                for t in sorted(buy_trades, key=lambda x: x.notional, reverse=True)[:5]
            ],
            'top_sell_trades': [
                {
                    'ticker': t.ticker,
                    'notional': t.notional,
                    'cost': t.transaction_cost,
                }
                for t in sorted(sell_trades, key=lambda x: x.notional, reverse=True)[:5]
            ],
        }
