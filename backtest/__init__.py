"""
Backtest Engine - Portfolio Construction Module

Provides portfolio construction, signal generation, and rebalancing logic
for Thai SET reverse DCF backtest following Damodaran's time-varying principles.
"""

from .signal_generator import (
    SignalGenerator,
    SignalScoringConfig,
    Signal,
)
from .portfolio_constructor import (
    PortfolioConstructor,
    EqualWeightConstructor,
    PositionSizingMethod,
    DiversificationRule,
    PortfolioConfig,
    Position,
    Portfolio,
)
from .rebalancer import (
    Rebalancer,
    RebalanceConfig,
    TransactionCostModel,
    Trade,
    RebalanceResult,
)
from .visualizer import (
    BacktestVisualizer,
    VisualizationConfig,
    BacktestSnapshot,
    PerformanceMetrics,
    export_visualization_data,
)
from .engine import (
    ThaiSETBacktestEngine,
    BacktestConfig,
    EnginePerformanceMetrics,
    BacktestResult,
)

__all__ = [
    'SignalGenerator',
    'SignalScoringConfig',
    'Signal',
    'PortfolioConstructor',
    'EqualWeightConstructor',
    'PositionSizingMethod',
    'DiversificationRule',
    'PortfolioConfig',
    'Position',
    'Portfolio',
    'Rebalancer',
    'RebalanceConfig',
    'TransactionCostModel',
    'Trade',
    'RebalanceResult',
    'BacktestVisualizer',
    'VisualizationConfig',
    'BacktestSnapshot',
    'PerformanceMetrics',
    'export_visualization_data',
    'ThaiSETBacktestEngine',
    'BacktestConfig',
    'EnginePerformanceMetrics',
    'BacktestResult',
]
