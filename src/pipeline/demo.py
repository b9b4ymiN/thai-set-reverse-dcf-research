from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

import pandas as pd

from src.pipeline.backtest import DEFAULT_HORIZONS, ReverseDCFBacktester
from src.pipeline.backtest_analysis import BacktestAnalysis
from src.pipeline.backtest_visuals import BacktestVisualizer
from src.pipeline.thesis_bundle import ThesisBundleBuilder


DEFAULT_DEMO_WACC_VALUES = (0.07, 0.08, 0.09)


@dataclass
class BacktestDemoRunner:
    horizons: Sequence[int] = DEFAULT_HORIZONS
    top_n: int = 2
    rebalance_frequency: str = 'QS'
    start_date: str = '2025-01-01'
    end_date: str = '2025-10-01'
    wacc_values: Sequence[float] = DEFAULT_DEMO_WACC_VALUES

    def run(self, output_dir: str = 'research_data/demo', include_bundle: bool = True) -> Dict[str, object]:
        output_root = Path(output_dir)
        dataset_dir = output_root / 'dataset'
        backtest_dir = output_root / 'backtest'
        bundle_dir = output_root / 'bundle'

        dataset_manifest = self._write_demo_dataset(dataset_dir)

        backtester = ReverseDCFBacktester(
            snapshot_path=str(dataset_dir / 'fundamentals_snapshot.csv'),
            observations_path=str(dataset_dir / 'fundamental_observations.csv'),
            price_history_path=str(dataset_dir / 'price_history.csv'),
            benchmark_history_path=str(dataset_dir / 'benchmark_history.csv'),
            default_wacc=0.08,
            wacc_mode='fixed',
        )
        backtest_result = backtester.run(
            output_dir=str(backtest_dir),
            horizons=self.horizons,
            top_n=self.top_n,
            rebalance_frequency=self.rebalance_frequency,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        analysis = BacktestAnalysis(
            snapshot_path=str(dataset_dir / 'fundamentals_snapshot.csv'),
            portfolio_returns_path=str(backtest_dir / 'portfolio_returns.csv'),
            summary_path=str(backtest_dir / 'summary.csv'),
            holdings_dir=str(backtest_dir),
        )
        sector_summary = analysis.build_sector_summary()
        sensitivity_summary = analysis.build_sensitivity_summary(
            snapshot_path=str(dataset_dir / 'fundamentals_snapshot.csv'),
            observations_path=str(dataset_dir / 'fundamental_observations.csv'),
            price_history_path=str(dataset_dir / 'price_history.csv'),
            benchmark_history_path=str(dataset_dir / 'benchmark_history.csv'),
            output_root=str(backtest_dir / 'sensitivity_runs'),
            wacc_values=self.wacc_values,
            top_n=self.top_n,
            horizons=self.horizons,
            rebalance_frequency=self.rebalance_frequency,
            start_date=self.start_date,
        )

        sector_path = backtest_dir / 'sector_summary.csv'
        sensitivity_path = backtest_dir / 'wacc_sensitivity.csv'
        appendix_path = backtest_dir / 'appendix.md'
        analysis_manifest_path = backtest_dir / 'analysis_manifest.json'

        sector_summary.to_csv(sector_path, index=False, encoding='utf-8-sig')
        sensitivity_summary.to_csv(sensitivity_path, index=False, encoding='utf-8-sig')
        appendix_path.write_text(
            BacktestAnalysis.build_appendix(sector_summary, sensitivity_summary),
            encoding='utf-8',
        )
        analysis_manifest = {
            'sector_summary_rows': int(len(sector_summary)),
            'wacc_sensitivity_rows': int(len(sensitivity_summary)),
            'wacc_values': list(self.wacc_values),
            'paths': {
                'sector_summary': str(sector_path),
                'wacc_sensitivity': str(sensitivity_path),
                'appendix': str(appendix_path),
            },
        }
        analysis_manifest_path.write_text(json.dumps(analysis_manifest, indent=2), encoding='utf-8')

        figure_manifest = BacktestVisualizer(
            summary_path=str(backtest_dir / 'summary.csv'),
            sector_summary_path=str(sector_path),
            sensitivity_path=str(sensitivity_path),
        ).generate(output_dir=str(backtest_dir / 'figures'))

        bundle_manifest = None
        if include_bundle:
            bundle_manifest = ThesisBundleBuilder(files=self._bundle_files(backtest_dir)).build(output_dir=str(bundle_dir))

        manifest = {
            'output_dir': str(output_root),
            'dataset': dataset_manifest,
            'backtest': backtest_result,
            'analysis': analysis_manifest,
            'figures': figure_manifest,
            'bundle': bundle_manifest,
            'paths': {
                'dataset_dir': str(dataset_dir),
                'backtest_dir': str(backtest_dir),
                'bundle_dir': str(bundle_dir),
                'readme': str(output_root / 'README.md'),
                'manifest': str(output_root / 'demo_manifest.json'),
            },
        }
        (output_root / 'README.md').write_text(self._build_readme(manifest), encoding='utf-8')
        (output_root / 'demo_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        return manifest

    def _write_demo_dataset(self, output_dir: Path) -> Dict[str, object]:
        output_dir.mkdir(parents=True, exist_ok=True)

        snapshot = pd.DataFrame([
            {'Ticker': 'VALUE.BK', 'Company_Name': 'Value Public Co.', 'Sector': 'Utilities', 'WACC': 0.08, 'Current_Price': 18.0},
            {'Ticker': 'STEADY.BK', 'Company_Name': 'Steady Healthcare', 'Sector': 'Healthcare', 'WACC': 0.08, 'Current_Price': 14.0},
            {'Ticker': 'CYCLIC.BK', 'Company_Name': 'Cyclic Energy', 'Sector': 'Energy', 'WACC': 0.08, 'Current_Price': 10.0},
        ])
        observations = pd.DataFrame(self._observation_rows())
        prices = pd.DataFrame(self._price_rows())
        benchmark = pd.DataFrame(self._benchmark_rows())

        paths = {
            'snapshot': output_dir / 'fundamentals_snapshot.csv',
            'observations': output_dir / 'fundamental_observations.csv',
            'prices': output_dir / 'price_history.csv',
            'benchmark': output_dir / 'benchmark_history.csv',
            'manifest': output_dir / 'manifest.json',
        }

        snapshot.to_csv(paths['snapshot'], index=False, encoding='utf-8-sig')
        observations.to_csv(paths['observations'], index=False, encoding='utf-8-sig')
        prices.to_csv(paths['prices'], index=False, encoding='utf-8-sig')
        benchmark.to_csv(paths['benchmark'], index=False, encoding='utf-8-sig')

        manifest = {
            'tickers': snapshot['Ticker'].tolist(),
            'rows': {
                'snapshot': int(len(snapshot)),
                'observations': int(len(observations)),
                'prices': int(len(prices)),
                'benchmark': int(len(benchmark)),
            },
            'paths': {name: str(path) for name, path in paths.items()},
        }
        paths['manifest'].write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        return manifest

    @staticmethod
    def _observation_rows() -> List[Dict[str, object]]:
        templates = {
            'VALUE.BK': {
                'Sector': 'Utilities',
                'fcf': [120.0, 126.0, 132.0, 140.0],
                'debt': 40.0,
                'cash': 8.0,
                'growth': [0.09, 0.11, 0.13, 0.15],
            },
            'STEADY.BK': {
                'Sector': 'Healthcare',
                'fcf': [80.0, 82.0, 85.0, 87.0],
                'debt': 24.0,
                'cash': 4.0,
                'growth': [0.05, 0.05, 0.04, 0.03],
            },
            'CYCLIC.BK': {
                'Sector': 'Energy',
                'fcf': [60.0, 58.0, 56.0, 54.0],
                'debt': 16.0,
                'cash': 2.0,
                'growth': [0.02, 0.00, -0.02, -0.04],
            },
        }
        periods = [
            ('2024-09-30', '2024-11-14'),
            ('2024-12-31', '2025-02-14'),
            ('2025-03-31', '2025-05-15'),
            ('2025-06-30', '2025-08-14'),
        ]

        rows: List[Dict[str, object]] = []
        for ticker, values in templates.items():
            for index, (statement_date, availability_date) in enumerate(periods):
                debt = values['debt']
                cash = values['cash']
                rows.append({
                    'Ticker': ticker,
                    'Period_Type': 'quarterly',
                    'Statement_Date': statement_date,
                    'Availability_Date': availability_date,
                    'Reporting_Lag_Days': 45,
                    'Revenue': 1000 + (index * 25),
                    'EBIT': 120 + (index * 10),
                    'FCF': values['fcf'][index],
                    'Total_Debt': debt,
                    'Total_Cash': cash,
                    'Net_Debt': debt - cash,
                    'Shares_Issued': 10.0,
                    'Diluted_Average_Shares': 10.0,
                    'Revenue_Growth': values['growth'][index],
                })
        return rows

    @staticmethod
    def _price_rows() -> List[Dict[str, object]]:
        dates = pd.date_range('2025-01-01', '2026-10-01', freq='MS')
        price_map = {
            'VALUE.BK': [18.0, 18.6, 19.1, 19.8, 20.4, 21.0, 21.7, 22.5, 23.3, 24.0, 24.8, 25.6, 26.5, 27.3, 28.1, 28.9, 29.8, 30.6, 31.5, 32.4, 33.2, 34.1],
            'STEADY.BK': [14.0, 14.1, 14.3, 14.4, 14.6, 14.8, 15.0, 15.2, 15.3, 15.5, 15.7, 15.9, 16.1, 16.3, 16.5, 16.7, 16.9, 17.1, 17.3, 17.5, 17.7, 17.9],
            'CYCLIC.BK': [10.0, 9.8, 9.6, 9.4, 9.5, 9.3, 9.1, 9.0, 9.2, 9.1, 9.0, 8.9, 9.1, 9.3, 9.2, 9.4, 9.6, 9.8, 9.9, 10.1, 10.3, 10.5],
        }
        rows: List[Dict[str, object]] = []
        for ticker, prices in price_map.items():
            for date_value, close in zip(dates, prices):
                rows.append({
                    'Date': date_value.date().isoformat(),
                    'Ticker': ticker,
                    'Open': close,
                    'High': close,
                    'Low': close,
                    'Close': close,
                    'Adj Close': close,
                    'Volume': 100000,
                })
        return rows

    @staticmethod
    def _benchmark_rows() -> List[Dict[str, object]]:
        dates = pd.date_range('2025-01-01', '2026-10-01', freq='MS')
        closes = [100.0, 100.6, 101.0, 101.4, 101.9, 102.3, 102.9, 103.4, 104.0, 104.5, 105.0, 105.6, 106.1, 106.7, 107.2, 107.8, 108.3, 108.9, 109.4, 109.9, 110.5, 111.0]
        rows: List[Dict[str, object]] = []
        for date_value, close in zip(dates, closes):
            rows.append({
                'Date': date_value.date().isoformat(),
                'Ticker': '^SET.BK',
                'Open': close,
                'High': close,
                'Low': close,
                'Close': close,
                'Adj Close': close,
                'Volume': 1000000,
            })
        return rows

    @staticmethod
    def _bundle_files(backtest_dir: Path) -> List[str]:
        return [
            'docs/thesis-methodology.md',
            'docs/thesis-results.md',
            'docs/executive-summary.md',
            'docs/presentation-script.md',
            'docs/defense-outline.md',
            'docs/q-and-a-sheet.md',
            str(backtest_dir / 'report.md'),
            str(backtest_dir / 'appendix.md'),
            str(backtest_dir / 'summary.csv'),
            str(backtest_dir / 'exclusions.csv'),
            str(backtest_dir / 'no_lookahead_audit.md'),
            str(backtest_dir / 'sector_summary.csv'),
            str(backtest_dir / 'wacc_sensitivity.csv'),
            str(backtest_dir / 'figures' / 'active_return_by_horizon.png'),
            str(backtest_dir / 'figures' / 'hit_rate_by_horizon.png'),
            str(backtest_dir / 'figures' / 'sector_active_return_heatmap.png'),
            str(backtest_dir / 'figures' / 'wacc_sensitivity.png'),
        ]

    @staticmethod
    def _build_readme(manifest: Dict[str, object]) -> str:
        paths = manifest['paths']
        lines = [
            '# Reverse DCF Demo Bundle',
            '',
            'This directory was generated by `python3 -m src.pipeline.demo`.',
            'It uses a deterministic local dataset and does not require any network access.',
            '',
            '## Included outputs',
            '',
            f"- Dataset bundle: `{paths['dataset_dir']}`",
            f"- Backtest outputs: `{paths['backtest_dir']}`",
            f"- Thesis-style bundle: `{paths['bundle_dir']}`",
            '',
            '## Suggested walkthrough',
            '',
            '1. Open `backtest/summary.csv` for the horizon-level results.',
            '2. Review `backtest/no_lookahead_audit.md` for the dating control.',
            '3. Open `backtest/figures/` for thesis-ready charts.',
            '4. Use `bundle/` as the compact handoff folder.',
            '',
        ]
        return '\n'.join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build a deterministic local demo for the Thai SET reverse-DCF backtest pipeline.')
    parser.add_argument('--output-dir', default='research_data/demo')
    parser.add_argument('--no-bundle', action='store_true', help='Skip thesis bundle packaging.')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runner = BacktestDemoRunner()
    manifest = runner.run(output_dir=args.output_dir, include_bundle=not args.no_bundle)
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
