"""
Signal Generator for Reverse DCF Backtest

Generates investment signals based on reverse DCF analysis with screening criteria.
Follows Damodaran's time-varying principles with no lookahead bias.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Callable
import pandas as pd
import numpy as np


@dataclass
class SignalScoringConfig:
    """Configuration for signal scoring and screening."""

    # Fundamental quality filters
    min_roe: float = 0.08  # Minimum ROE (8%)
    min_fcf: float = 0  # Minimum FCF (accept 0 for growth stocks)
    max_debt_to_equity: float = 3.0  # Maximum debt-to-equity ratio

    # Valuation filters
    max_pe_ratio: float = 50.0  # Maximum P/E ratio
    max_pb_ratio: float = 10.0  # Maximum P/B ratio
    min_market_cap: float = 0  # Minimum market cap (accept all)

    # Growth filters
    min_revenue_growth: float = -0.5  # Allow declining businesses (max -50%)
    max_implied_growth: float = 0.50  # Maximum implied growth (50%)

    # Signal scoring weights
    growth_differential_weight: float = 1.0
    roe_weight: float = 0.3
    fcf_yield_weight: float = 0.2
    quality_weight: float = 0.2

    # Damodaran principles
    use_sector_hurdle_rates: bool = True
    quality_over_quantity: bool = True
    avoid_lookahead_bias: bool = True


@dataclass
class Signal:
    """Generated investment signal for a stock."""

    ticker: str
    signal_date: datetime
    score: float
    rank: int
    raw_growth_differential: float
    adjusted_score: float
    quality_score: float
    valuation_score: float

    # Fundamental data
    price: float
    fcf: float
    shares: float
    wacc: float
    implied_growth: float
    actual_revenue_growth: float
    roe: float
    debt_to_equity: float
    pe_ratio: float
    pb_ratio: float
    market_cap: float

    # Metadata
    sector: Optional[str] = None
    industry: Optional[str] = None
    passed_screening: bool = True
    screening_reasons: List[str] = field(default_factory=list)
    no_lookahead_pass: bool = True


class SignalGenerator:
    """
    Generate investment signals using reverse DCF analysis.

    Applies screening criteria based on fundamentals, valuation, and growth.
    Scores stocks using growth differential (actual - implied growth) adjusted
    for quality factors.

    Attributes:
        config: SignalScoringConfig with screening thresholds
        sector_hurdle_rates: Dict mapping sectors to WACC adjustments
    """

    def __init__(
        self,
        config: Optional[SignalScoringConfig] = None,
        sector_hurdle_rates: Optional[Dict[str, float]] = None,
    ):
        """Initialize signal generator with configuration."""
        self.config = config or SignalScoringConfig()
        self.sector_hurdle_rates = sector_hurdle_rates or self._default_sector_hurdle_rates()

    def _default_sector_hurdle_rates(self) -> Dict[str, float]:
        """
        Default sector-specific WACC adjustments for emerging markets.

        Based on Damodaran's industry betas for emerging markets.
        Higher risk sectors get higher hurdle rates.
        """
        return {
            # Technology - Higher growth, higher risk
            'Technology': 0.015,
            'Telecommunications': 0.010,

            # Financials - Regulated, moderate risk
            'Financials': 0.005,
            'Banks': 0.005,
            'Insurance': 0.008,

            # Consumer - Stable demand
            'Consumer Staples': 0.000,
            'Consumer Discretionary': 0.005,

            # Healthcare - Defensive
            'Healthcare': 0.002,

            # Industrials - Cyclical
            'Industrials': 0.008,
            'Auto & Components': 0.012,

            # Energy - Commodity risk
            'Energy': 0.015,
            'Oil & Gas': 0.018,

            # Materials - Cyclical
            'Materials': 0.012,
            'Chemicals': 0.010,

            # Utilities - Regulated, stable
            'Utilities': 0.002,
            'Real Estate': 0.008,

            # Infrastructure - Mixed
            'Infrastructure': 0.006,
        }

    def generate_signals(
        self,
        cross_section: pd.DataFrame,
        rebalance_date: datetime,
        snapshot_data: Optional[pd.DataFrame] = None,
    ) -> Tuple[List[Signal], pd.DataFrame]:
        """
        Generate investment signals from a cross-section of stocks.

        Args:
            cross_section: DataFrame with reverse DCF results
            rebalance_date: Date of signal generation
            snapshot_data: Optional snapshot with sector/industry info

        Returns:
            Tuple of (list of Signal objects, filtered DataFrame)
        """
        signals = []
        filtered_rows = []

        for _, row in cross_section.iterrows():
            ticker = row.get('Ticker')
            if not ticker:
                continue

            # Enrich with snapshot data if available
            sector_info = self._get_sector_info(ticker, snapshot_data)
            row = row.copy()
            row['Sector'] = sector_info.get('sector')
            row['Industry'] = sector_info.get('industry')

            # Apply screening criteria
            passed, reasons = self._screen_stock(row, rebalance_date)

            # Calculate signal scores
            raw_score = self._calculate_raw_score(row)
            quality_score = self._calculate_quality_score(row)
            valuation_score = self._calculate_valuation_score(row)
            adjusted_score = self._calculate_adjusted_score(
                raw_score, quality_score, valuation_score
            )

            signal = Signal(
                ticker=ticker,
                signal_date=rebalance_date,
                score=adjusted_score,
                rank=0,  # Will be assigned after sorting
                raw_growth_differential=row.get('Signal_Score', 0),
                adjusted_score=adjusted_score,
                quality_score=quality_score,
                valuation_score=valuation_score,
                price=row.get('Price', 0),
                fcf=row.get('FCF', 0),
                shares=row.get('Shares', 0),
                wacc=row.get('WACC', 0),
                implied_growth=row.get('Implied_Growth_Rate', 0),
                actual_revenue_growth=row.get('Actual_Revenue_Growth', 0),
                roe=row.get('ROE', 0),
                debt_to_equity=row.get('Debt_to_Equity', 0),
                pe_ratio=self._extract_ratio(row, 'PE_Ratio'),
                pb_ratio=self._extract_ratio(row, 'PB_Ratio'),
                market_cap=row.get('Market_Cap', 0),
                sector=sector_info.get('sector'),
                industry=sector_info.get('industry'),
                passed_screening=passed,
                screening_reasons=reasons,
                no_lookahead_pass=row.get('No_Lookahead_Pass', True),
            )

            if passed or not self.config.quality_over_quantity:
                signals.append(signal)
                filtered_rows.append(row.to_dict())

        # Rank signals by adjusted score
        signals.sort(key=lambda s: s.score, reverse=True)
        for i, signal in enumerate(signals):
            signal.rank = i + 1

        filtered_df = pd.DataFrame(filtered_rows) if filtered_rows else pd.DataFrame()
        return signals, filtered_df

    def _get_sector_info(
        self,
        ticker: str,
        snapshot_data: Optional[pd.DataFrame],
    ) -> Dict[str, Optional[str]]:
        """Extract sector and industry info from snapshot."""
        if snapshot_data is None or snapshot_data.empty:
            return {'sector': None, 'industry': None}

        row = snapshot_data[snapshot_data['Ticker'] == ticker]
        if row.empty:
            return {'sector': None, 'industry': None}

        return {
            'sector': row.iloc[0].get('Sector'),
            'industry': row.iloc[0].get('Industry'),
        }

    def _screen_stock(
        self,
        row: pd.Series,
        rebalance_date: datetime,
    ) -> Tuple[bool, List[str]]:
        """
        Apply screening criteria to determine if stock qualifies.

        Returns tuple of (passed, list of failure reasons).
        """
        reasons = []

        # Fundamental quality checks
        roe = row.get('ROE', 0)
        if pd.isna(roe) or roe < self.config.min_roe:
            reasons.append(f'ROE {roe:.2%} < {self.config.min_roe:.0%}')

        debt_to_equity = row.get('Debt_to_Equity', 0)
        if pd.notna(debt_to_equity) and debt_to_equity > self.config.max_debt_to_equity:
            reasons.append(f'D/E {debt_to_equity:.2f} > {self.config.max_debt_to_equity}')

        # Valuation checks
        pe_ratio = self._extract_ratio(row, 'PE_Ratio')
        if pd.notna(pe_ratio) and pe_ratio > self.config.max_pe_ratio:
            reasons.append(f'P/E {pe_ratio:.1f} > {self.config.max_pe_ratio}')

        pb_ratio = self._extract_ratio(row, 'PB_Ratio')
        if pd.notna(pb_ratio) and pb_ratio > self.config.max_pb_ratio:
            reasons.append(f'P/B {pb_ratio:.1f} > {self.config.max_pb_ratio}')

        # Growth sanity checks
        implied_growth = row.get('Implied_Growth_Rate', 0)
        if pd.notna(implied_growth) and implied_growth > self.config.max_implied_growth:
            reasons.append(f'Implied growth {implied_growth:.2%} > {self.config.max_implied_growth:.0%}')

        # Revenue growth check (allow declining but not collapsing)
        revenue_growth = row.get('Actual_Revenue_Growth', 0)
        if pd.notna(revenue_growth) and revenue_growth < self.config.min_revenue_growth:
            reasons.append(f'Revenue growth {revenue_growth:.2%} < {self.config.min_revenue_growth:.0%}')

        # Lookahead bias check (Damodaran principle)
        if self.config.avoid_lookahead_bias:
            no_lookahead_pass = row.get('No_Lookahead_Pass', True)
            if not no_lookahead_pass:
                reasons.append('Failed no-lookahead validation')

        passed = len(reasons) == 0
        return passed, reasons

    def _calculate_raw_score(self, row: pd.Series) -> float:
        """
        Calculate raw signal score based on growth differential.

        Growth Differential = Actual Revenue Growth - Implied Growth Rate
        Negative differential = market pessimism (potential opportunity)
        Positive differential = market optimism (caution)
        """
        return row.get('Signal_Score', 0)

    def _calculate_quality_score(self, row: pd.Series) -> float:
        """
        Calculate quality score based on fundamentals.

        Higher ROE, lower debt, positive FCF = higher quality.
        """
        score = 0.0

        # ROE contribution (up to 0.4)
        roe = row.get('ROE', 0)
        if pd.notna(roe) and roe > 0:
            score += min(roe / 0.20, 1.0) * 0.4

        # Debt quality (up to 0.3)
        debt_to_equity = row.get('Debt_to_Equity', 0)
        if pd.notna(debt_to_equity):
            score += max(1 - (debt_to_equity / 2.0), 0) * 0.3

        # FCF positive (up to 0.3)
        fcf = row.get('FCF', 0)
        if pd.notna(fcf) and fcf > 0:
            score += 0.3

        return score

    def _calculate_valuation_score(self, row: pd.Series) -> float:
        """
        Calculate valuation score.

        Lower P/E and P/B = better value.
        """
        score = 0.0

        # P/E score (lower is better, up to 0.5)
        pe_ratio = self._extract_ratio(row, 'PE_Ratio')
        if pd.notna(pe_ratio) and pe_ratio > 0:
            score += min(15 / pe_ratio, 1.0) * 0.5

        # P/B score (lower is better, up to 0.5)
        pb_ratio = self._extract_ratio(row, 'PB_Ratio')
        if pd.notna(pb_ratio) and pb_ratio > 0:
            score += min(3 / pb_ratio, 1.0) * 0.5

        return score

    def _calculate_adjusted_score(
        self,
        raw_score: float,
        quality_score: float,
        valuation_score: float,
    ) -> float:
        """
        Calculate final adjusted score combining all factors.

        Lower (more negative) growth differential = better opportunity
        Quality and valuation provide positive adjustments.
        """
        config = self.config

        # Base score from growth differential (inverted so negative = good)
        base_score = -raw_score * config.growth_differential_weight

        # Add quality and valuation bonuses
        adjusted = base_score + (quality_score * config.quality_weight) + \
                   (valuation_score * config.fcf_yield_weight)

        return adjusted

    def _extract_ratio(self, row: pd.Series, column: str) -> Optional[float]:
        """Safely extract ratio value from row."""
        value = row.get(column)
        if pd.isna(value) or value == 0:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def adjust_wacc_for_sector(self, base_wacc: float, sector: Optional[str]) -> float:
        """
        Adjust WACC based on sector-specific hurdle rates (Damodaran principle).

        Args:
            base_wacc: Base WACC (e.g., Thailand country rate)
            sector: Stock's sector

        Returns:
            Adjusted WACC for sector
        """
        if not self.config.use_sector_hurdle_rates or sector is None:
            return base_wacc

        adjustment = self.sector_hurdle_rates.get(sector, 0)
        return base_wacc + adjustment

    def get_signal_summary(self, signals: List[Signal]) -> Dict[str, any]:
        """
        Generate summary statistics for generated signals.

        Returns dict with counts, scores, and sector distribution.
        """
        if not signals:
            return {
                'total_signals': 0,
                'passed_screening': 0,
                'failed_screening': 0,
                'avg_score': 0,
                'sector_distribution': {},
            }

        passed = [s for s in signals if s.passed_screening]
        sectors = {}

        for signal in signals:
            sector = signal.sector or 'Unknown'
            sectors[sector] = sectors.get(sector, 0) + 1

        return {
            'total_signals': len(signals),
            'passed_screening': len(passed),
            'failed_screening': len(signals) - len(passed),
            'avg_score': np.mean([s.score for s in signals]),
            'avg_raw_differential': np.mean([s.raw_growth_differential for s in signals]),
            'sector_distribution': sectors,
            'top_10_tickers': [s.ticker for s in signals[:10]],
        }
