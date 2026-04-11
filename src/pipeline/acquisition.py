from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence

import pandas as pd
import yfinance as yf

from rdcf.data_pipeline import PRICE_COLUMNS, ResearchDataPipeline
from rdcf.data_sources import (
    YahooFinanceSource,
    build_datasource_quality_report,
    build_reverse_dcf_exclusion_report,
    build_validation_references,
)

from .provenance import (
    PRIMARY_SOURCE_ID,
    append_acquisition_log,
    file_inventory,
    format_timestamp,
    source_review_payload,
    summarize_quality,
    utc_now,
    write_json,
)


FUNDAMENTAL_ITEM_UNITS = {
    "Revenue": "THB",
    "EBIT": "THB",
    "FCF": "THB",
    "Total_Debt": "THB",
    "Total_Cash": "THB",
    "Net_Debt": "THB",
    "Shares_Issued": "shares",
    "Diluted_Average_Shares": "shares",
    "Revenue_Growth": "ratio",
}


@dataclass
class AcquisitionPipeline:
    source: YahooFinanceSource = field(default_factory=YahooFinanceSource)
    history_downloader: Callable[..., pd.DataFrame] = yf.download
    benchmark_ticker: str = "^SET.BK"
    reporting_lag_days: int = 45

    def run(
        self,
        tickers: Sequence[str],
        output_root: str = "data",
        raw_universe: str = "set100",
        period: str = "10y",
        interval: str = "1d",
        benchmark_ticker: Optional[str] = None,
    ) -> Dict[str, object]:
        requested_tickers = ResearchDataPipeline._deduplicate_tickers(list(tickers))
        benchmark = benchmark_ticker or self.benchmark_ticker
        acquired_at = utc_now()
        acquired_at_str = format_timestamp(acquired_at)
        run_id = f"acq-{acquired_at.strftime('%Y%m%dT%H%M%SZ')}"
        root = Path(output_root)

        helper = ResearchDataPipeline(
            source=self.source,
            history_downloader=self.history_downloader,
            benchmark_ticker=benchmark,
            reporting_lag_days=self.reporting_lag_days,
        )

        bundle_rows = [
            self.source.fetch_ticker_bundle(ticker, reporting_lag_days=self.reporting_lag_days)
            for ticker in requested_tickers
        ]
        fundamentals = pd.DataFrame([row["snapshot"] for row in bundle_rows if row.get("snapshot")])
        observations = helper.build_fundamental_observations(bundle_rows)
        quality = build_datasource_quality_report(fundamentals)
        exclusions = build_reverse_dcf_exclusion_report(fundamentals)
        validations = pd.DataFrame(build_validation_references(requested_tickers))
        fundamental_coverage = helper.build_fundamental_coverage_report(requested_tickers, observations)
        price_history = helper.download_price_history(requested_tickers, period=period, interval=interval)
        benchmark_history = helper.download_price_history([benchmark], period=period, interval=interval)
        price_coverage = helper.build_price_coverage_report(requested_tickers, price_history)

        raw_paths = self._write_raw_layer(
            root=root,
            raw_universe=raw_universe,
            tickers=requested_tickers,
            bundle_rows=bundle_rows,
            price_history=price_history,
            benchmark=benchmark,
            benchmark_history=benchmark_history,
            validations=validations,
            acquired_at=acquired_at_str,
        )
        processed_paths = self._write_processed_layer(
            root=root,
            observations=observations,
            price_history=price_history,
            benchmark_history=benchmark_history,
            acquired_at=acquired_at_str,
        )
        metadata_paths = self._write_metadata_layer(
            root=root,
            run_id=run_id,
            requested_tickers=requested_tickers,
            benchmark=benchmark,
            period=period,
            interval=interval,
            fundamentals=fundamentals,
            observations=observations,
            quality=quality,
            exclusions=exclusions,
            validations=validations,
            fundamental_coverage=fundamental_coverage,
            price_coverage=price_coverage,
            raw_paths=raw_paths,
            processed_paths=processed_paths,
            acquired_at=acquired_at_str,
        )

        return {
            "run_id": run_id,
            "acquired_at": acquired_at_str,
            "primary_source": PRIMARY_SOURCE_ID,
            "tickers": requested_tickers,
            "benchmark_ticker": benchmark,
            "paths": {**{key: str(value) for key, value in raw_paths.items()}, **{key: str(value) for key, value in processed_paths.items()}, **{key: str(value) for key, value in metadata_paths.items()}},
            "row_counts": {
                "fundamentals_snapshot": int(len(fundamentals)),
                "fundamental_observations": int(len(observations)),
                "price_history": int(len(price_history)),
                "benchmark_history": int(len(benchmark_history)),
            },
        }

    def _write_raw_layer(
        self,
        *,
        root: Path,
        raw_universe: str,
        tickers: Sequence[str],
        bundle_rows: Sequence[Dict[str, object]],
        price_history: pd.DataFrame,
        benchmark: str,
        benchmark_history: pd.DataFrame,
        validations: pd.DataFrame,
        acquired_at: str,
    ) -> Dict[str, Path]:
        raw_root = root / "raw" / raw_universe
        paths: Dict[str, Path] = {}
        validation_lookup = validations.set_index("Ticker").to_dict("index") if not validations.empty else {}

        for ticker, bundle in zip(tickers, bundle_rows):
            ticker_dir = raw_root / ticker
            ticker_dir.mkdir(parents=True, exist_ok=True)
            payload = {
                "ticker": ticker,
                "source": PRIMARY_SOURCE_ID,
                "fetched_at": acquired_at,
                "snapshot": bundle.get("snapshot"),
                "observations": self._frame_records(bundle.get("observations")),
                "validation_reference": validation_lookup.get(ticker, {}),
            }
            fundamentals_path = ticker_dir / "fundamentals.json"
            write_json(fundamentals_path, payload)
            ticker_prices = price_history.loc[price_history["Ticker"] == ticker] if not price_history.empty else pd.DataFrame(columns=PRICE_COLUMNS)
            prices_path = ticker_dir / "prices.csv"
            ticker_prices.to_csv(prices_path, index=False, encoding="utf-8-sig")
            paths[f"raw_{ticker}_fundamentals"] = fundamentals_path
            paths[f"raw_{ticker}_prices"] = prices_path

        benchmark_dir = root / "raw" / "benchmarks"
        benchmark_dir.mkdir(parents=True, exist_ok=True)
        benchmark_path = benchmark_dir / f"{self._safe_filename(benchmark)}.csv"
        benchmark_history.to_csv(benchmark_path, index=False, encoding="utf-8-sig")
        paths["raw_benchmark_prices"] = benchmark_path
        return paths

    def _write_processed_layer(
        self,
        *,
        root: Path,
        observations: pd.DataFrame,
        price_history: pd.DataFrame,
        benchmark_history: pd.DataFrame,
        acquired_at: str,
    ) -> Dict[str, Path]:
        processed_root = root / "processed"
        quarterly_path = processed_root / "fundamentals" / "quarterly" / "fundamentals.parquet"
        annual_path = processed_root / "fundamentals" / "annual" / "fundamentals.parquet"
        quarterly_meta = processed_root / "fundamentals" / "quarterly" / "metadata.json"
        annual_meta = processed_root / "fundamentals" / "annual" / "metadata.json"
        daily_prices_path = processed_root / "prices" / "daily" / "prices.parquet"
        adjusted_prices_path = processed_root / "prices" / "adjusted" / "prices.parquet"

        for directory in [quarterly_path.parent, annual_path.parent, daily_prices_path.parent, adjusted_prices_path.parent]:
            directory.mkdir(parents=True, exist_ok=True)

        long_fundamentals = self._normalize_fundamental_records(observations, acquired_at)
        quarterly = long_fundamentals.loc[long_fundamentals["period_type"] == "quarterly"].copy()
        annual = long_fundamentals.loc[long_fundamentals["period_type"] == "annual"].copy()
        quarterly.to_parquet(quarterly_path, index=False)
        annual.to_parquet(annual_path, index=False)

        write_json(
            quarterly_meta,
            self._build_period_metadata("quarterly", quarterly, acquired_at),
        )
        write_json(
            annual_meta,
            self._build_period_metadata("annual", annual, acquired_at),
        )

        all_prices = self._normalize_price_records(price_history, benchmark_history, acquired_at)
        adjusted_prices = self._build_adjusted_price_records(all_prices)
        all_prices.to_parquet(daily_prices_path, index=False)
        adjusted_prices.to_parquet(adjusted_prices_path, index=False)
        return {
            "processed_quarterly_fundamentals": quarterly_path,
            "processed_quarterly_metadata": quarterly_meta,
            "processed_annual_fundamentals": annual_path,
            "processed_annual_metadata": annual_meta,
            "processed_daily_prices": daily_prices_path,
            "processed_adjusted_prices": adjusted_prices_path,
        }

    def _write_metadata_layer(
        self,
        *,
        root: Path,
        run_id: str,
        requested_tickers: Sequence[str],
        benchmark: str,
        period: str,
        interval: str,
        fundamentals: pd.DataFrame,
        observations: pd.DataFrame,
        quality: pd.DataFrame,
        exclusions: pd.DataFrame,
        validations: pd.DataFrame,
        fundamental_coverage: pd.DataFrame,
        price_coverage: pd.DataFrame,
        raw_paths: Dict[str, Path],
        processed_paths: Dict[str, Path],
        acquired_at: str,
    ) -> Dict[str, Path]:
        metadata_root = root / "processed" / "metadata"
        metadata_root.mkdir(parents=True, exist_ok=True)

        quality_path = metadata_root / "quality_report.csv"
        exclusions_path = metadata_root / "reverse_dcf_exclusions.csv"
        validation_path = metadata_root / "set_validation_references.csv"
        fundamental_coverage_path = metadata_root / "fundamental_coverage.csv"
        price_coverage_path = metadata_root / "price_coverage.csv"
        manifest_path = metadata_root / "data_manifest.json"
        acquisition_log_path = metadata_root / "acquisition_log.json"

        quality.to_csv(quality_path, index=False, encoding="utf-8-sig")
        exclusions.to_csv(exclusions_path, index=False, encoding="utf-8-sig")
        validations.to_csv(validation_path, index=False, encoding="utf-8-sig")
        fundamental_coverage.to_csv(fundamental_coverage_path, index=False, encoding="utf-8-sig")
        price_coverage.to_csv(price_coverage_path, index=False, encoding="utf-8-sig")

        all_paths = {
            **raw_paths,
            **processed_paths,
            "metadata_quality_report": quality_path,
            "metadata_reverse_dcf_exclusions": exclusions_path,
            "metadata_validation_references": validation_path,
            "metadata_fundamental_coverage": fundamental_coverage_path,
            "metadata_price_coverage": price_coverage_path,
        }

        manifest = {
            "run_id": run_id,
            "acquired_at": acquired_at,
            "primary_source": PRIMARY_SOURCE_ID,
            "requested_tickers": list(requested_tickers),
            "benchmark_ticker": benchmark,
            "period": period,
            "interval": interval,
            "reporting_lag_days": self.reporting_lag_days,
            "source_review": source_review_payload(),
            "quality_summary": summarize_quality(quality, exclusions, fundamental_coverage, price_coverage),
            "rows": {
                "fundamentals_snapshot": int(len(fundamentals)),
                "fundamental_observations": int(len(observations)),
                "quality_report": int(len(quality)),
                "reverse_dcf_exclusions": int(len(exclusions)),
                "validation_references": int(len(validations)),
                "fundamental_coverage": int(len(fundamental_coverage)),
                "price_coverage": int(len(price_coverage)),
            },
            "files": file_inventory(all_paths),
        }
        write_json(manifest_path, manifest)

        log_record = {
            "run_id": run_id,
            "acquired_at": acquired_at,
            "primary_source": PRIMARY_SOURCE_ID,
            "requested_tickers": list(requested_tickers),
            "benchmark_ticker": benchmark,
            "period": period,
            "interval": interval,
            "reporting_lag_days": self.reporting_lag_days,
            "source_review": source_review_payload(),
            "quality_summary": manifest["quality_summary"],
        }
        append_acquisition_log(acquisition_log_path, log_record)
        return {
            "metadata_quality_report": quality_path,
            "metadata_reverse_dcf_exclusions": exclusions_path,
            "metadata_validation_references": validation_path,
            "metadata_fundamental_coverage": fundamental_coverage_path,
            "metadata_price_coverage": price_coverage_path,
            "metadata_manifest": manifest_path,
            "metadata_acquisition_log": acquisition_log_path,
        }

    @staticmethod
    def _frame_records(frame: object) -> List[Dict[str, object]]:
        if not isinstance(frame, pd.DataFrame) or frame.empty:
            return []
        records = frame.where(pd.notna(frame), None).to_dict(orient="records")
        return records

    @staticmethod
    def _safe_filename(value: str) -> str:
        return value.replace("^", "").replace("/", "_")

    @staticmethod
    def _build_period_metadata(period_type: str, frame: pd.DataFrame, acquired_at: str) -> Dict[str, object]:
        return {
            "period_type": period_type,
            "primary_source": PRIMARY_SOURCE_ID,
            "updated_at": acquired_at,
            "row_count": int(len(frame)),
            "ticker_count": int(frame["ticker"].nunique()) if not frame.empty else 0,
            "item_count": int(frame["item_name"].nunique()) if not frame.empty else 0,
        }

    @staticmethod
    def _normalize_fundamental_records(observations: pd.DataFrame, acquired_at: str) -> pd.DataFrame:
        rows: List[Dict[str, object]] = []
        if observations.empty:
            return pd.DataFrame(
                columns=[
                    "ticker",
                    "period_type",
                    "fiscal_date",
                    "report_date",
                    "item_name",
                    "value",
                    "unit",
                    "source",
                    "updated_at",
                ]
            )

        for _, observation in observations.iterrows():
            for item_name, unit in FUNDAMENTAL_ITEM_UNITS.items():
                rows.append(
                    {
                        "ticker": observation["Ticker"],
                        "period_type": observation["Period_Type"],
                        "fiscal_date": observation["Statement_Date"],
                        "report_date": observation["Availability_Date"],
                        "item_name": item_name.lower(),
                        "value": observation.get(item_name),
                        "unit": unit,
                        "source": PRIMARY_SOURCE_ID,
                        "updated_at": acquired_at,
                    }
                )

        frame = pd.DataFrame(rows)
        frame["fiscal_date"] = pd.to_datetime(frame["fiscal_date"])
        frame["report_date"] = pd.to_datetime(frame["report_date"])
        frame["updated_at"] = pd.to_datetime(frame["updated_at"])
        return frame

    @staticmethod
    def _normalize_price_records(price_history: pd.DataFrame, benchmark_history: pd.DataFrame, acquired_at: str) -> pd.DataFrame:
        frames = []
        for frame, is_benchmark in ((price_history, False), (benchmark_history, True)):
            if frame.empty:
                continue
            normalized = frame.rename(
                columns={
                    "Date": "date",
                    "Ticker": "ticker",
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Adj Close": "adj_close",
                    "Volume": "volume",
                }
            ).copy()
            normalized["date"] = pd.to_datetime(normalized["date"])
            normalized["source"] = PRIMARY_SOURCE_ID
            normalized["updated_at"] = pd.to_datetime(acquired_at)
            normalized["is_benchmark"] = is_benchmark
            frames.append(normalized)

        if not frames:
            return pd.DataFrame(
                columns=["date", "ticker", "open", "high", "low", "close", "adj_close", "volume", "source", "updated_at", "is_benchmark"]
            )
        return pd.concat(frames, ignore_index=True, sort=False)[
            ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume", "source", "updated_at", "is_benchmark"]
        ]

    @staticmethod
    def _build_adjusted_price_records(frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame(
                columns=["date", "ticker", "close", "adj_close", "volume", "source", "updated_at", "is_benchmark", "price_basis"]
            )
        adjusted = frame[["date", "ticker", "close", "adj_close", "volume", "source", "updated_at", "is_benchmark"]].copy()
        adjusted["price_basis"] = "adj_close_available"
        return adjusted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Acquire Thai stock fundamentals and price data with provenance tracking.")
    parser.add_argument("--tickers", nargs="*", default=None, help="Ticker list (defaults to SETStockFetcher universe).")
    parser.add_argument("--output-root", default="data", help="Root folder for raw/processed outputs.")
    parser.add_argument("--raw-universe", default="set100", help="Subfolder name under data/raw/ for ticker payloads.")
    parser.add_argument("--period", default="10y", help="Yahoo history period, e.g. 1y, 5y, 10y, max.")
    parser.add_argument("--interval", default="1d", help="Yahoo interval.")
    parser.add_argument("--benchmark", default="^SET.BK", help="Benchmark ticker.")
    parser.add_argument("--reporting-lag-days", type=int, default=45, help="Assumed statement availability lag.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.tickers is None:
        from set_stock_fetcher import SETStockFetcher

        tickers = SETStockFetcher.SET_TICKERS
    else:
        tickers = args.tickers

    pipeline = AcquisitionPipeline(benchmark_ticker=args.benchmark, reporting_lag_days=args.reporting_lag_days)
    manifest = pipeline.run(
        tickers=tickers,
        output_root=args.output_root,
        raw_universe=args.raw_universe,
        period=args.period,
        interval=args.interval,
        benchmark_ticker=args.benchmark,
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
