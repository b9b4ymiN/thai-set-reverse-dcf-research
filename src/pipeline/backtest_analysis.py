from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import pandas as pd

from src.pipeline.backtest import DEFAULT_HORIZONS, ReverseDCFBacktester


@dataclass
class BacktestAnalysis:
    snapshot_path: str = 'research_data/latest/fundamentals_snapshot.csv'
    portfolio_returns_path: str = 'research_data/latest/backtest/portfolio_returns.csv'
    summary_path: str = 'research_data/latest/backtest/summary.csv'
    holdings_dir: str = 'research_data/latest/backtest'

    def __post_init__(self) -> None:
        self.snapshot = pd.read_csv(self.snapshot_path)
        self.portfolio_returns = pd.read_csv(self.portfolio_returns_path)
        self.summary = pd.read_csv(self.summary_path)
        detail_frames = []
        for path in sorted(Path(self.holdings_dir).glob('portfolio_*m.csv')):
            detail_frames.append(pd.read_csv(path))
        self.portfolio_details = pd.concat(detail_frames, ignore_index=True, sort=False) if detail_frames else pd.DataFrame()

    def build_sector_summary(self) -> pd.DataFrame:
        if self.portfolio_details.empty:
            return pd.DataFrame(columns=['Sector', 'Horizon_Months', 'Mean_Forward_Return', 'Mean_Active_Return', 'Selections'])
        merged = self.portfolio_details.merge(
            self.snapshot[['Ticker', 'Sector']],
            on='Ticker',
            how='left',
        )
        sector_summary = merged.groupby(['Sector', 'Horizon_Months']).agg(
            Mean_Forward_Return=('Forward_Return', 'mean'),
            Mean_Active_Return=('Active_Return', 'mean'),
            Selections=('Ticker', 'count'),
        ).reset_index().sort_values(['Horizon_Months', 'Mean_Active_Return'], ascending=[True, False])
        return sector_summary

    def build_sensitivity_summary(
        self,
        snapshot_path: str,
        observations_path: str,
        price_history_path: str,
        benchmark_history_path: str,
        output_root: str,
        wacc_values: Sequence[float] = (0.06, 0.08, 0.10),
        top_n: int = 10,
        horizons: Sequence[int] = DEFAULT_HORIZONS,
        rebalance_frequency: str = 'Q',
        start_date: str | None = '2020-01-01',
    ) -> pd.DataFrame:
        rows: List[Dict[str, object]] = []
        base_output = Path(output_root)
        base_output.mkdir(parents=True, exist_ok=True)
        for wacc in wacc_values:
            output_dir = base_output / f'wacc_{int(round(wacc * 100)):02d}'
            backtester = ReverseDCFBacktester(
                snapshot_path=snapshot_path,
                observations_path=observations_path,
                price_history_path=price_history_path,
                benchmark_history_path=benchmark_history_path,
                default_wacc=wacc,
                wacc_mode='fixed',
            )
            result = backtester.run(
                output_dir=str(output_dir),
                horizons=horizons,
                top_n=top_n,
                rebalance_frequency=rebalance_frequency,
                start_date=start_date,
            )
            summary = pd.read_csv(output_dir / 'summary.csv')
            for _, row in summary.iterrows():
                rows.append({
                    'WACC_Assumption': wacc,
                    'Horizon_Months': int(row['Horizon_Months']),
                    'Portfolio_Return': float(row['Portfolio_Return']),
                    'Benchmark_Return': float(row['Benchmark_Return']),
                    'Active_Return': float(row['Active_Return']),
                    'Hit_Rate': float(row['Hit_Rate']),
                    'Observations': int(row['Observations']),
                    'Backtest_Output': str(output_dir),
                    'Signals': result['signals'],
                })
        return pd.DataFrame(rows).sort_values(['Horizon_Months', 'WACC_Assumption']).reset_index(drop=True)

    @staticmethod
    def build_appendix(sector_summary: pd.DataFrame, sensitivity_summary: pd.DataFrame) -> str:
        lines = ['# Backtest Appendix', '']
        lines.append('## Sector Summary')
        lines.append('')
        if sector_summary.empty:
            lines.append('No sector summary available.')
        else:
            lines.extend(_markdown_table(sector_summary))
        lines.append('')
        lines.append('## WACC Sensitivity')
        lines.append('')
        if sensitivity_summary.empty:
            lines.append('No sensitivity summary available.')
        else:
            lines.extend(_markdown_table(sensitivity_summary))
        lines.append('')
        return '\n'.join(lines)


def _markdown_table(df: pd.DataFrame) -> List[str]:
    columns = list(df.columns)
    rows = ['| ' + ' | '.join(columns) + ' |', '| ' + ' | '.join(['---'] * len(columns)) + ' |']
    for _, row in df.iterrows():
        rows.append('| ' + ' | '.join(str(row[column]) for column in columns) + ' |')
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Generate sector and sensitivity analysis from backtest outputs.')
    parser.add_argument('--snapshot-path', default='research_data/latest/fundamentals_snapshot.csv')
    parser.add_argument('--portfolio-returns-path', default='research_data/latest/backtest/portfolio_returns.csv')
    parser.add_argument('--summary-path', default='research_data/latest/backtest/summary.csv')
    parser.add_argument('--observations-path', default='research_data/latest/fundamental_observations.csv')
    parser.add_argument('--price-history-path', default='research_data/latest/price_history.csv')
    parser.add_argument('--benchmark-history-path', default='research_data/latest/benchmark_history.csv')
    parser.add_argument('--output-dir', default='research_data/latest/backtest')
    parser.add_argument('--top-n', type=int, default=10)
    parser.add_argument('--horizons', nargs='*', type=int, default=list(DEFAULT_HORIZONS))
    parser.add_argument('--wacc-values', nargs='*', type=float, default=[0.06, 0.08, 0.10])
    parser.add_argument('--rebalance-frequency', default='Q')
    parser.add_argument('--start-date', default='2020-01-01')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    analysis = BacktestAnalysis(
        snapshot_path=args.snapshot_path,
        portfolio_returns_path=args.portfolio_returns_path,
        summary_path=args.summary_path,
        holdings_dir=args.output_dir,
    )
    sector_summary = analysis.build_sector_summary()
    sensitivity_summary = analysis.build_sensitivity_summary(
        snapshot_path=args.snapshot_path,
        observations_path=args.observations_path,
        price_history_path=args.price_history_path,
        benchmark_history_path=args.benchmark_history_path,
        output_root=str(output_dir / 'sensitivity_runs'),
        wacc_values=args.wacc_values,
        top_n=args.top_n,
        horizons=args.horizons,
        rebalance_frequency=args.rebalance_frequency,
        start_date=args.start_date,
    )

    sector_path = output_dir / 'sector_summary.csv'
    sensitivity_path = output_dir / 'wacc_sensitivity.csv'
    appendix_path = output_dir / 'appendix.md'
    manifest_path = output_dir / 'analysis_manifest.json'

    sector_summary.to_csv(sector_path, index=False, encoding='utf-8-sig')
    sensitivity_summary.to_csv(sensitivity_path, index=False, encoding='utf-8-sig')
    appendix_path.write_text(BacktestAnalysis.build_appendix(sector_summary, sensitivity_summary), encoding='utf-8')
    manifest = {
        'sector_summary_rows': int(len(sector_summary)),
        'wacc_sensitivity_rows': int(len(sensitivity_summary)),
        'wacc_values': args.wacc_values,
        'paths': {
            'sector_summary': str(sector_path),
            'wacc_sensitivity': str(sensitivity_path),
            'appendix': str(appendix_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
