from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import pandas as pd

from rdcf.data_pipeline import PRICE_COLUMNS, ResearchDataPipeline
from rdcf.data_sources import (
    build_datasource_quality_report,
    build_reverse_dcf_exclusion_report,
    build_validation_references,
)
from rdcf.data_sources.stockanalysis_source import (
    STOCKANALYSIS_SOURCE_ID,
    CachedYahooBundleSource,
    StockAnalysisHybridSource,
)


@dataclass
class SourceOfTruthBundleBuilder:
    source: StockAnalysisHybridSource = field(default_factory=StockAnalysisHybridSource)
    raw_price_root: str = "data/raw/set100"
    benchmark_price_path: str = "data/raw/benchmarks/SET.BK.csv"
    benchmark_ticker: str = "^SET.BK"
    reporting_lag_days: int = 45

    def build(
        self,
        tickers: Sequence[str],
        output_dir: str = "research_data/source_of_truth_100",
    ) -> Dict[str, object]:
        tickers = ResearchDataPipeline._deduplicate_tickers(list(tickers))
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        bundle_rows = [
            self.source.fetch_ticker_bundle(ticker, reporting_lag_days=self.reporting_lag_days)
            for ticker in tickers
        ]
        fundamentals = pd.DataFrame([row["snapshot"] for row in bundle_rows if row.get("snapshot")])
        observations = ResearchDataPipeline.build_fundamental_observations(bundle_rows)
        provenance = self._concat_frames([row.get("provenance") for row in bundle_rows])
        source_coverage = pd.DataFrame([row.get("coverage", {}) for row in bundle_rows])

        quality = build_datasource_quality_report(fundamentals)
        exclusions = build_reverse_dcf_exclusion_report(fundamentals)
        validations = pd.DataFrame(build_validation_references(tickers))
        fundamental_coverage = ResearchDataPipeline.build_fundamental_coverage_report(tickers, observations)

        price_history = self._load_cached_price_history(tickers)
        benchmark_history = self._load_benchmark_history()
        price_coverage = ResearchDataPipeline.build_price_coverage_report(tickers, price_history)
        provenance_summary = self._build_provenance_summary(provenance)

        paths = {
            "fundamentals": output_path / "fundamentals_snapshot.csv",
            "quality": output_path / "datasource_quality.csv",
            "exclusions": output_path / "reverse_dcf_exclusions.csv",
            "validation": output_path / "set_validation_references.csv",
            "observations": output_path / "fundamental_observations.csv",
            "provenance": output_path / "fundamental_provenance.csv",
            "provenance_summary": output_path / "fundamental_source_summary.csv",
            "source_coverage": output_path / "quarterly_source_coverage.csv",
            "fundamental_coverage": output_path / "fundamental_coverage.csv",
            "prices": output_path / "price_history.csv",
            "benchmark": output_path / "benchmark_history.csv",
            "price_coverage": output_path / "price_coverage.csv",
            "manifest": output_path / "manifest.json",
        }

        fundamentals.to_csv(paths["fundamentals"], index=False, encoding="utf-8-sig")
        quality.to_csv(paths["quality"], index=False, encoding="utf-8-sig")
        exclusions.to_csv(paths["exclusions"], index=False, encoding="utf-8-sig")
        validations.to_csv(paths["validation"], index=False, encoding="utf-8-sig")
        observations.to_csv(paths["observations"], index=False, encoding="utf-8-sig")
        provenance.to_csv(paths["provenance"], index=False, encoding="utf-8-sig")
        provenance_summary.to_csv(paths["provenance_summary"], index=False, encoding="utf-8-sig")
        source_coverage.to_csv(paths["source_coverage"], index=False, encoding="utf-8-sig")
        fundamental_coverage.to_csv(paths["fundamental_coverage"], index=False, encoding="utf-8-sig")
        price_history.to_csv(paths["prices"], index=False, encoding="utf-8-sig")
        benchmark_history.to_csv(paths["benchmark"], index=False, encoding="utf-8-sig")
        price_coverage.to_csv(paths["price_coverage"], index=False, encoding="utf-8-sig")

        manifest = {
            "primary_source": STOCKANALYSIS_SOURCE_ID,
            "fallback_source": "yahoo_yfinance_cached_raw",
            "benchmark_ticker": self.benchmark_ticker,
            "reporting_lag_days": self.reporting_lag_days,
            "tickers": tickers,
            "rows": {
                "fundamentals": int(len(fundamentals)),
                "observations": int(len(observations)),
                "provenance": int(len(provenance)),
                "source_coverage": int(len(source_coverage)),
                "prices": int(len(price_history)),
                "benchmark": int(len(benchmark_history)),
            },
            "coverage_summary": {
                "stockanalysis_ticker_count": int(source_coverage["StockAnalysis_File_Available"].sum()) if not source_coverage.empty else 0,
                "fallback_only_ticker_count": int((~source_coverage["StockAnalysis_File_Available"]).sum()) if not source_coverage.empty else 0,
                "quarterly_start_date": self._safe_min(source_coverage.get("Quarterly_Start_Date")),
                "quarterly_end_date": self._safe_max(source_coverage.get("Quarterly_End_Date")),
                "missing_price_tickers": price_coverage.loc[~price_coverage["Has_Prices"], "Ticker"].tolist(),
            },
            "paths": {name: str(path) for name, path in paths.items()},
        }
        paths["manifest"].write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    def _load_cached_price_history(self, tickers: Sequence[str]) -> pd.DataFrame:
        frames: List[pd.DataFrame] = []
        for ticker in tickers:
            path = Path(self.raw_price_root) / ticker / "prices.csv"
            if not path.exists():
                continue
            frame = pd.read_csv(path)
            for column in PRICE_COLUMNS:
                if column not in frame.columns:
                    frame[column] = pd.NA
            frames.append(frame[PRICE_COLUMNS])
        if not frames:
            return pd.DataFrame(columns=PRICE_COLUMNS)
        history = pd.concat(frames, ignore_index=True, sort=False)
        history["Date"] = pd.to_datetime(history["Date"]).dt.date.astype(str)
        return history

    def _load_benchmark_history(self) -> pd.DataFrame:
        path = Path(self.benchmark_price_path)
        if not path.exists():
            return pd.DataFrame(columns=PRICE_COLUMNS)
        frame = pd.read_csv(path)
        if "Ticker" not in frame.columns:
            frame["Ticker"] = self.benchmark_ticker
        for column in PRICE_COLUMNS:
            if column not in frame.columns:
                frame[column] = pd.NA
        frame["Date"] = pd.to_datetime(frame["Date"]).dt.date.astype(str)
        return frame[PRICE_COLUMNS]

    @staticmethod
    def _concat_frames(frames: Sequence[object]) -> pd.DataFrame:
        valid = [frame for frame in frames if isinstance(frame, pd.DataFrame) and not frame.empty]
        if not valid:
            return pd.DataFrame()
        return pd.concat(valid, ignore_index=True, sort=False)

    @staticmethod
    def _build_provenance_summary(provenance: pd.DataFrame) -> pd.DataFrame:
        if provenance.empty:
            return pd.DataFrame(
                columns=["Source", "Period_Type", "Item_Name", "Row_Count", "Ticker_Count", "First_Statement_Date", "Last_Statement_Date"]
            )
        summary = (
            provenance.groupby(["Source", "Period_Type", "Item_Name"], dropna=False)
            .agg(
                Row_Count=("Ticker", "size"),
                Ticker_Count=("Ticker", "nunique"),
                First_Statement_Date=("Statement_Date", "min"),
                Last_Statement_Date=("Statement_Date", "max"),
            )
            .reset_index()
            .sort_values(["Source", "Period_Type", "Item_Name"])
        )
        return summary

    @staticmethod
    def _safe_min(series: Optional[pd.Series]) -> str:
        if series is None or series.empty:
            return ""
        cleaned = series.replace("", pd.NA).dropna()
        return str(cleaned.min()) if not cleaned.empty else ""

    @staticmethod
    def _safe_max(series: Optional[pd.Series]) -> str:
        if series is None or series.empty:
            return ""
        cleaned = series.replace("", pd.NA).dropna()
        return str(cleaned.max()) if not cleaned.empty else ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the scraping-first 100-stock source-of-truth bundle.")
    parser.add_argument("--tickers-from-manifest", default="data/processed/metadata/data_manifest.json")
    parser.add_argument("--output-dir", default="research_data/source_of_truth_100")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_payload = json.loads(Path(args.tickers_from_manifest).read_text(encoding="utf-8"))
    tickers = manifest_payload.get("requested_tickers") or manifest_payload.get("tickers") or []
    builder = SourceOfTruthBundleBuilder()
    manifest = builder.build(tickers=tickers, output_dir=args.output_dir)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
