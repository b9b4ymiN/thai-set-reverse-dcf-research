"""
Portfolio Constructor Module

Builds portfolios from ranked signals using position sizing and diversification rules.
Implements Damodaran's quality-over-quantity principle.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
import pandas as pd
import numpy as np


class PositionSizingMethod(Enum):
    """Methods for sizing positions in the portfolio."""

    EQUAL_WEIGHT = "equal_weight"  # All positions same size
    SIGNAL_WEIGHTED = "signal_weighted"  # Weight by signal strength
    MARKET_CAP_WEIGHTED = "market_cap_weighted"  # Weight by market cap
    INVERSE_VOLATILITY = "inverse_volatility"  # Weight by inverse volatility
    QUALITY_WEIGHTED = "quality_weighted"  # Weight by quality score


class DiversificationRule(Enum):
    """Diversification constraints for portfolio construction."""

    SECTOR_LIMIT = "sector_limit"  # Max exposure per sector
    INDUSTRY_LIMIT = "industry_limit"  # Max exposure per industry
    MAX_POSITION = "max_position"  # Max size of single position
    MIN_POSITION = "min_position"  # Min size for inclusion


@dataclass
class PortfolioConfig:
    """Configuration for portfolio construction."""

    # Portfolio size
    max_positions: int = 20  # Maximum number of stocks
    min_positions: int = 10  # Minimum number of stocks (or use cash)

    # Position sizing
    sizing_method: PositionSizingMethod = PositionSizingMethod.EQUAL_WEIGHT
    max_position_weight: float = 0.15  # Max 15% in single stock
    min_position_weight: float = 0.01  # Min 1% for inclusion

    # Diversification
    max_sector_exposure: float = 0.40  # Max 40% per sector
    max_industry_exposure: float = 0.25  # Max 25% per industry
    min_sectors: int = 4  # Minimum number of sectors

    # Damodaran principles
    quality_over_quantity: bool = True
    require_diversification: bool = True
    use_sector_hurdle_rates: bool = True

    # Cash handling
    allow_cash: bool = True
    cash_weight: float = 0.05  # Target 5% cash buffer

    # Turnover control
    max_turnover: float = 0.50  # Max 50% annual turnover


@dataclass
class Position:
    """A single position in the portfolio."""

    ticker: str
    weight: float
    entry_price: float
    shares: Optional[int] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    signal_score: Optional[float] = None
    quality_score: Optional[float] = None
    reason: Optional[str] = None  # Why this position was included


@dataclass
class Portfolio:
    """A constructed portfolio with metadata."""

    positions: List[Position]
    as_of_date: datetime
    total_weight: float
    cash_weight: float
    metadata: Dict = field(default_factory=dict)

    @property
    def tickers(self) -> List[str]:
        """Get list of tickers in portfolio."""
        return [p.ticker for p in self.positions]

    @property
    def sector_weights(self) -> Dict[str, float]:
        """Calculate total weight per sector."""
        weights = {}
        for pos in self.positions:
            sector = pos.sector or 'Unknown'
            weights[sector] = weights.get(sector, 0) + pos.weight
        return weights

    @property
    def industry_weights(self) -> Dict[str, float]:
        """Calculate total weight per industry."""
        weights = {}
        for pos in self.positions:
            industry = pos.industry or 'Unknown'
            weights[industry] = weights.get(industry, 0) + pos.weight
        return weights

    def to_dataframe(self) -> pd.DataFrame:
        """Convert portfolio to DataFrame for analysis."""
        rows = []
        for pos in self.positions:
            rows.append({
                'Ticker': pos.ticker,
                'Weight': pos.weight,
                'Entry_Price': pos.entry_price,
                'Shares': pos.shares,
                'Sector': pos.sector,
                'Industry': pos.industry,
                'Signal_Score': pos.signal_score,
                'Quality_Score': pos.quality_score,
                'Reason': pos.reason,
            })
        return pd.DataFrame(rows)


class PortfolioConstructor:
    """
    Construct portfolios from ranked signals.

    Implements position sizing and diversification rules following
    Damodaran's principles: quality over quantity, proper diversification,
    and risk-conscious positioning.
    """

    def __init__(self, config: Optional[PortfolioConfig] = None):
        """Initialize portfolio constructor with configuration."""
        self.config = config or PortfolioConfig()

    def construct_portfolio(
        self,
        signals: List,
        as_of_date: datetime,
        previous_portfolio: Optional[Portfolio] = None,
    ) -> Portfolio:
        """
        Construct a portfolio from ranked signals.

        Args:
            signals: List of Signal objects, ranked by score
            as_of_date: Portfolio construction date
            previous_portfolio: Previous portfolio for turnover control

        Returns:
            Constructed Portfolio object
        """
        if not signals:
            return self._empty_portfolio(as_of_date)

        # Select top N signals based on config
        selected = self._select_signals(signals)

        # Apply quality filter if configured
        if self.config.quality_over_quantity:
            selected = self._apply_quality_filter(selected)

        # Calculate position weights
        weights = self._calculate_weights(selected)

        # Apply diversification constraints
        weights = self._apply_diversification_constraints(
            selected, weights
        )

        # Build position objects
        positions = []
        for signal, weight in zip(selected, weights):
            if weight >= self.config.min_position_weight:
                pos = Position(
                    ticker=signal.ticker,
                    weight=weight,
                    entry_price=signal.price,
                    sector=signal.sector,
                    industry=signal.industry,
                    signal_score=signal.score,
                    quality_score=signal.quality_score,
                    reason=f"Rank {signal.rank}, Score: {signal.score:.3f}",
                )
                positions.append(pos)

        # Calculate cash allocation
        total_weight = sum(p.weight for p in positions)
        cash_weight = 0.0
        if self.config.allow_cash:
            cash_weight = max(0, self.config.cash_weight - (1.0 - total_weight))

        # Build metadata
        metadata = {
            'total_signals': len(signals),
            'qualified_signals': len(selected),
            'selected_positions': len(positions),
            'avg_signal_score': np.mean([s.score for s in selected]) if selected else 0,
            'sector_count': len(set(p.sector for p in positions if p.sector)),
            'industry_count': len(set(p.industry for p in positions if p.industry)),
            'construction_method': self.config.sizing_method.value,
        }

        return Portfolio(
            positions=positions,
            as_of_date=as_of_date,
            total_weight=total_weight,
            cash_weight=cash_weight,
            metadata=metadata,
        )

    def _select_signals(self, signals: List) -> List:
        """Select top N signals from ranked list."""
        max_n = self.config.max_positions
        min_n = self.config.min_positions

        # Take top max_n, but ensure at least min_n if available
        selected = signals[:max(max_n, min_n)]

        # If quality over quantity, we might end up with fewer
        if self.config.quality_over_quantity:
            # Only keep signals that passed screening
            selected = [s for s in selected if s.passed_screening]

            # If we have too few qualified, lower standards gradually
            if len(selected) < min_n and len(signals) >= min_n:
                # Expand to min_n even if some failed screening
                selected = signals[:min_n]

        return selected

    def _apply_quality_filter(self, signals: List) -> List:
        """
        Apply additional quality filters following Damodaran's principle.

        Focus on best opportunities rather than filling positions.
        """
        if not signals:
            return signals

        # Require minimum signal quality
        qualified = []
        for signal in signals:
            # Must have reasonable signal score
            if signal.score < -0.3:  # Too pessimistic
                continue

            # Must have reasonable valuation
            if signal.pe_ratio and signal.pe_ratio > 50:
                continue

            # Must have reasonable quality
            if signal.quality_score < 0.2:
                continue

            qualified.append(signal)

        # Ensure we have at least some positions
        min_qualified = min(len(qualified), self.config.min_positions)
        if min_qualified == 0 and signals:
            # If nothing qualified, take top 5
            return signals[:5]

        return qualified[:min_qualified]

    def _calculate_weights(self, signals: List) -> List[float]:
        """Calculate position weights based on configured method."""
        if not signals:
            return []

        method = self.config.sizing_method

        if method == PositionSizingMethod.EQUAL_WEIGHT:
            return self._equal_weights(signals)

        elif method == PositionSizingMethod.SIGNAL_WEIGHTED:
            return self._signal_weighted(signals)

        elif method == PositionSizingMethod.MARKET_CAP_WEIGHTED:
            return self._market_cap_weighted(signals)

        elif method == PositionSizingMethod.QUALITY_WEIGHTED:
            return self._quality_weighted(signals)

        else:  # Default to equal weight
            return self._equal_weights(signals)

    def _equal_weights(self, signals: List) -> List[float]:
        """Equal weight for all positions."""
        n = len(signals)
        target_weight = 1.0 / n
        return [min(target_weight, self.config.max_position_weight)] * n

    def _signal_weighted(self, signals: List) -> List[float]:
        """Weight by signal score (higher score = larger weight)."""
        scores = np.array([s.score for s in signals])
        # Shift to positive
        if scores.min() < 0:
            scores = scores - scores.min() + 0.01

        # Normalize
        weights = scores / scores.sum()

        # Cap max position size
        weights = np.minimum(weights, self.config.max_position_weight)

        # Renormalize
        weights = weights / weights.sum()

        return weights.tolist()

    def _market_cap_weighted(self, signals: List) -> List[float]:
        """Weight by market cap (larger caps get smaller weights)."""
        market_caps = np.array([s.market_cap for s in signals])

        # Avoid division by zero
        market_caps = np.maximum(market_caps, 1e6)

        # Inverse weighting (smaller caps = higher weight)
        inv_mc = 1.0 / market_caps
        weights = inv_mc / inv_mc.sum()

        # Cap max position size
        weights = np.minimum(weights, self.config.max_position_weight)

        # Renormalize
        weights = weights / weights.sum()

        return weights.tolist()

    def _quality_weighted(self, signals: List) -> List[float]:
        """Weight by quality score."""
        quality_scores = np.array([s.quality_score for s in signals])

        # Normalize
        if quality_scores.sum() == 0:
            return self._equal_weights(signals)

        weights = quality_scores / quality_scores.sum()

        # Cap max position size
        weights = np.minimum(weights, self.config.max_position_weight)

        # Renormalize
        weights = weights / weights.sum()

        return weights.tolist()

    def _apply_diversification_constraints(
        self,
        signals: List,
        weights: List[float],
    ) -> List[float]:
        """Apply sector/industry diversification constraints."""
        if not self.config.require_diversification:
            return weights

        # Build sector mapping
        sector_map = {}
        for i, signal in enumerate(signals):
            sector = signal.sector or 'Unknown'
            if sector not in sector_map:
                sector_map[sector] = []
            sector_map[sector].append(i)

        # Check and adjust sector exposures
        adjusted_weights = weights.copy()
        max_sector_weight = self.config.max_sector_exposure

        for sector, indices in sector_map.items():
            sector_weight = sum(adjusted_weights[i] for i in indices)

            if sector_weight > max_sector_weight:
                # Scale down this sector
                scale_factor = max_sector_weight / sector_weight
                for i in indices:
                    adjusted_weights[i] *= scale_factor

        # Renormalize
        total = sum(adjusted_weights)
        if total > 0:
            adjusted_weights = [w / total for w in adjusted_weights]

        return adjusted_weights

    def _empty_portfolio(self, as_of_date: datetime) -> Portfolio:
        """Create an empty (all-cash) portfolio."""
        return Portfolio(
            positions=[],
            as_of_date=as_of_date,
            total_weight=0.0,
            cash_weight=1.0,
            metadata={'reason': 'no_signals_available'},
        )

    def calculate_turnover(
        self,
        previous_portfolio: Portfolio,
        new_portfolio: Portfolio,
    ) -> float:
        """
        Calculate portfolio turnover.

        Turnover = (weight bought + weight sold) / 2
        """
        prev_positions = {p.ticker: p.weight for p in previous_portfolio.positions}
        new_positions = {p.ticker: p.weight for p in new_portfolio.positions}

        all_tickers = set(prev_positions.keys()) | set(new_positions.keys())

        buys = 0.0
        sells = 0.0

        for ticker in all_tickers:
            prev_weight = prev_positions.get(ticker, 0)
            new_weight = new_positions.get(ticker, 0)

            if new_weight > prev_weight:
                buys += (new_weight - prev_weight)
            elif new_weight < prev_weight:
                sells += (prev_weight - new_weight)

        return (buys + sells) / 2


class EqualWeightConstructor(PortfolioConstructor):
    """
    Simplified equal-weight portfolio constructor.

    All positions get equal weight. Simple and robust.
    """

    def __init__(self, max_positions: int = 20):
        """Initialize with max positions."""
        config = PortfolioConfig(
            max_positions=max_positions,
            sizing_method=PositionSizingMethod.EQUAL_WEIGHT,
        )
        super().__init__(config)
