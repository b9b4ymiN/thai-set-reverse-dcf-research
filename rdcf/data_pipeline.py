from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence

import pandas as pd
import yfinance as yf

from rdcf.data_sources import (
    YahooFinanceSource,
    build_datasource_quality_report,
    build_reverse_dcf_exclusion_report,
    build_validation_references,
)


PRICE_COLUMNS = ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']


@dataclass
class ResearchDataPipeline:
    source: YahooFinanceSource = field(default_factory=YahooFinanceSource)
    history_downloader: Callable[..., pd.DataFrame] = yf.download
    benchmark_ticker: str = '^SET.BK'
    reporting_lag_days: int = 45

    def build_research_dataset(
        self,
        tickers: Sequence[str],
        output_dir: str = 'research_data/latest',
        period: str = '10y',
        interval: str = '1d',
        benchmark_ticker: Optional[str] = None,
        sync_root_snapshot: bool = False,
    ) -> dict:
        tickers = self._deduplicate_tickers(tickers)
        benchmark = benchmark_ticker or self.benchmark_ticker
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        bundle_rows = [self.source.fetch_ticker_bundle(ticker, reporting_lag_days=self.reporting_lag_days) for ticker in tickers]
        fundamentals = pd.DataFrame([row['snapshot'] for row in bundle_rows if row['snapshot']])
        quality = build_datasource_quality_report(fundamentals)
        exclusions = build_reverse_dcf_exclusion_report(fundamentals)
        validations = pd.DataFrame(build_validation_references(fundamentals['Ticker'].tolist())) if not fundamentals.empty else pd.DataFrame()
        observations = self.build_fundamental_observations(bundle_rows)
        fundamental_coverage = self.build_fundamental_coverage_report(tickers, observations)
        price_history = self.download_price_history(tickers, period=period, interval=interval)
        benchmark_history = self.download_price_history([benchmark], period=period, interval=interval)
        price_coverage = self.build_price_coverage_report(tickers, price_history)

        paths = {
            'fundamentals': output_path / 'fundamentals_snapshot.csv',
            'quality': output_path / 'datasource_quality.csv',
            'exclusions': output_path / 'reverse_dcf_exclusions.csv',
            'validation': output_path / 'set_validation_references.csv',
            'observations': output_path / 'fundamental_observations.csv',
            'fundamental_coverage': output_path / 'fundamental_coverage.csv',
            'prices': output_path / 'price_history.csv',
            'benchmark': output_path / 'benchmark_history.csv',
            'price_coverage': output_path / 'price_coverage.csv',
            'manifest': output_path / 'manifest.json',
        }

        fundamentals.to_csv(paths['fundamentals'], index=False, encoding='utf-8-sig')
        quality.to_csv(paths['quality'], index=False, encoding='utf-8-sig')
        exclusions.to_csv(paths['exclusions'], index=False, encoding='utf-8-sig')
        validations.to_csv(paths['validation'], index=False, encoding='utf-8-sig')
        observations.to_csv(paths['observations'], index=False, encoding='utf-8-sig')
        fundamental_coverage.to_csv(paths['fundamental_coverage'], index=False, encoding='utf-8-sig')
        price_history.to_csv(paths['prices'], index=False, encoding='utf-8-sig')
        benchmark_history.to_csv(paths['benchmark'], index=False, encoding='utf-8-sig')
        price_coverage.to_csv(paths['price_coverage'], index=False, encoding='utf-8-sig')

        if sync_root_snapshot:
            self._sync_root_snapshot_outputs(
                fundamentals=fundamentals,
                quality=quality,
                exclusions=exclusions,
                validations=validations,
            )

        manifest = {
            'tickers': list(tickers),
            'benchmark_ticker': benchmark,
            'period': period,
            'interval': interval,
            'reporting_lag_days': self.reporting_lag_days,
            'rows': {
                'fundamentals': int(len(fundamentals)),
                'observations': int(len(observations)),
                'fundamental_coverage': int(len(fundamental_coverage)),
                'prices': int(len(price_history)),
                'benchmark': int(len(benchmark_history)),
                'price_coverage': int(len(price_coverage)),
            },
            'paths': {key: str(value) for key, value in paths.items()},
            'missing_fundamental_tickers': fundamental_coverage.loc[~fundamental_coverage['Has_Fundamental_Observations'], 'Ticker'].tolist(),
            'missing_price_tickers': price_coverage.loc[~price_coverage['Has_Prices'], 'Ticker'].tolist(),
            'root_snapshot_synced': sync_root_snapshot,
        }
        paths['manifest'].write_text(json.dumps(manifest, indent=2))
        return manifest

    @staticmethod
    def build_fundamental_observations(bundle_rows: Sequence[dict]) -> pd.DataFrame:
        frames = [
            row['observations']
            for row in bundle_rows
            if isinstance(row.get('observations'), pd.DataFrame) and not row['observations'].empty
        ]
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True, sort=False)

    def download_price_history(
        self,
        tickers: Iterable[str],
        period: str = '10y',
        interval: str = '1d',
        ) -> pd.DataFrame:
        tickers = self._deduplicate_tickers(list(tickers))
        if not tickers:
            return pd.DataFrame(columns=PRICE_COLUMNS)

        raw = self.history_downloader(
            tickers=tickers,
            period=period,
            interval=interval,
            group_by='ticker',
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        return self._normalize_price_history(raw, tickers)

    @staticmethod
    def _normalize_price_history(raw: pd.DataFrame, tickers: Sequence[str]) -> pd.DataFrame:
        if raw is None or raw.empty:
            return pd.DataFrame(columns=PRICE_COLUMNS)

        rows: List[pd.DataFrame] = []
        if isinstance(raw.columns, pd.MultiIndex):
            for ticker in tickers:
                if ticker not in raw.columns.get_level_values(0):
                    continue
                frame = raw[ticker].copy()
                frame['Date'] = frame.index
                frame['Ticker'] = ticker
                rows.append(frame.reset_index(drop=True))
        else:
            frame = raw.copy()
            frame['Date'] = frame.index
            frame['Ticker'] = tickers[0]
            rows.append(frame.reset_index(drop=True))

        if not rows:
            return pd.DataFrame(columns=PRICE_COLUMNS)

        history = pd.concat(rows, ignore_index=True, sort=False)
        for column in PRICE_COLUMNS:
            if column not in history.columns:
                history[column] = pd.NA
        history = history.dropna(subset=['Open', 'High', 'Low', 'Close', 'Adj Close'], how='all')
        history['Date'] = pd.to_datetime(history['Date']).dt.date.astype(str)
        return history[PRICE_COLUMNS]

    @staticmethod
    def build_price_coverage_report(requested_tickers: Sequence[str], history: pd.DataFrame) -> pd.DataFrame:
        requested_tickers = ResearchDataPipeline._deduplicate_tickers(list(requested_tickers))
        if history.empty:
            return pd.DataFrame(
                [{'Ticker': ticker, 'Price_Row_Count': 0, 'Has_Prices': False} for ticker in requested_tickers]
            )

        counts = history.groupby('Ticker').size().to_dict()
        return pd.DataFrame(
            [
                {
                    'Ticker': ticker,
                    'Price_Row_Count': int(counts.get(ticker, 0)),
                    'Has_Prices': ticker in counts,
                }
                for ticker in requested_tickers
            ]
        )

    @staticmethod
    def build_fundamental_coverage_report(requested_tickers: Sequence[str], observations: pd.DataFrame) -> pd.DataFrame:
        requested_tickers = ResearchDataPipeline._deduplicate_tickers(list(requested_tickers))
        if observations.empty:
            return pd.DataFrame(
                [
                    {'Ticker': ticker, 'Observation_Row_Count': 0, 'Has_Fundamental_Observations': False}
                    for ticker in requested_tickers
                ]
            )

        counts = observations.groupby('Ticker').size().to_dict()
        return pd.DataFrame(
            [
                {
                    'Ticker': ticker,
                    'Observation_Row_Count': int(counts.get(ticker, 0)),
                    'Has_Fundamental_Observations': ticker in counts,
                }
                for ticker in requested_tickers
            ]
        )

    @staticmethod
    def _deduplicate_tickers(tickers: Sequence[str]) -> List[str]:
        return list(dict.fromkeys(tickers))

    @staticmethod
    def _sync_root_snapshot_outputs(
        fundamentals: pd.DataFrame,
        quality: pd.DataFrame,
        exclusions: pd.DataFrame,
        validations: pd.DataFrame,
    ) -> None:
        fundamentals.to_csv('set_stock_data.csv', index=False, encoding='utf-8-sig')
        quality.to_csv('set_stock_data_quality.csv', index=False, encoding='utf-8-sig')
        exclusions.to_csv('reverse_dcf_input_exclusions.csv', index=False, encoding='utf-8-sig')
        validations.to_csv('set_validation_references.csv', index=False, encoding='utf-8-sig')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build a research-ready Thai reverse DCF data bundle.')
    parser.add_argument('--tickers', nargs='*', default=None, help='Ticker list (defaults to SETStockFetcher universe).')
    parser.add_argument('--output-dir', default='research_data/latest', help='Where to write the dataset bundle.')
    parser.add_argument('--period', default='10y', help='Yahoo history period, e.g. 5y, 10y, max.')
    parser.add_argument('--interval', default='1d', help='Yahoo history interval.')
    parser.add_argument('--benchmark', default='^SET.BK', help='Benchmark ticker for market history.')
    parser.add_argument('--reporting-lag-days', type=int, default=45, help='Assumed lag for current fundamental observations.')
    parser.add_argument('--sync-root-snapshot', action='store_true', help='Also write root-level snapshot CSVs used by reverse_dcf_model.py.')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.tickers is None:
        from set_stock_fetcher import SETStockFetcher
        tickers = SETStockFetcher.SET_TICKERS
    else:
        tickers = args.tickers

    pipeline = ResearchDataPipeline(benchmark_ticker=args.benchmark, reporting_lag_days=args.reporting_lag_days)
    manifest = pipeline.build_research_dataset(
        tickers=tickers,
        output_dir=args.output_dir,
        period=args.period,
        interval=args.interval,
        benchmark_ticker=args.benchmark,
        sync_root_snapshot=args.sync_root_snapshot,
    )
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
