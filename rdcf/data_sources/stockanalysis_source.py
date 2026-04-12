from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd

from .yahoo_source import (
    DEFAULT_SNAPSHOT_FIELDS,
    STATEMENT_OBSERVATION_FIELDS,
    YahooFinanceSource,
)


STOCKANALYSIS_SOURCE_ID = "stockanalysis_scraping"
YFINANCE_CACHE_SOURCE_ID = "yahoo_yfinance_cached_raw"
YFINANCE_LIVE_SOURCE_ID = "yahoo_yfinance_live"
DERIVED_SOURCE_ID = "derived_from_merged_observations"

CORE_FIELD_MAP = {
    "revenue": "Revenue",
    "ebit": "EBIT",
    "free_cash_flow": "FCF",
}

FALLBACK_ONLY_FIELDS = (
    "Total_Debt",
    "Total_Cash",
    "Net_Debt",
    "Shares_Issued",
    "Diluted_Average_Shares",
)

SNAPSHOT_OVERRIDE_FIELDS = ("Revenue", "EBIT", "FCF", "Revenue_Growth")


@dataclass
class CachedYahooBundleSource:
    raw_root: str = "data/raw/set100"
    live_source: Optional[YahooFinanceSource] = None

    def fetch_ticker_bundle(self, ticker: str, reporting_lag_days: int = 45) -> Dict[str, object]:
        cached_path = Path(self.raw_root) / ticker / "fundamentals.json"
        if cached_path.exists():
            payload = json.loads(cached_path.read_text(encoding="utf-8"))
            observations = pd.DataFrame(payload.get("observations", []))
            observations = self._normalize_observations(observations, reporting_lag_days)
            return {
                "snapshot": self._normalize_snapshot(payload.get("snapshot")),
                "observations": observations,
                "source_id": YFINANCE_CACHE_SOURCE_ID,
                "raw_path": str(cached_path),
            }

        if self.live_source is not None:
            bundle = self.live_source.fetch_ticker_bundle(ticker, reporting_lag_days=reporting_lag_days)
            bundle["source_id"] = YFINANCE_LIVE_SOURCE_ID
            bundle["raw_path"] = None
            bundle["observations"] = self._normalize_observations(bundle.get("observations"), reporting_lag_days)
            bundle["snapshot"] = self._normalize_snapshot(bundle.get("snapshot"))
            return bundle

        return {
            "snapshot": self._normalize_snapshot(None),
            "observations": pd.DataFrame(columns=STATEMENT_OBSERVATION_FIELDS),
            "source_id": YFINANCE_CACHE_SOURCE_ID,
            "raw_path": None,
        }

    @staticmethod
    def _normalize_snapshot(snapshot: Optional[Dict[str, object]]) -> Dict[str, object]:
        payload = dict(snapshot or {})
        for column in DEFAULT_SNAPSHOT_FIELDS:
            payload.setdefault(column, 0 if column not in {"Ticker", "Company_Name", "Sector", "Industry", "Fetched_Date"} else "")
        return payload

    @staticmethod
    def _normalize_observations(frame: object, reporting_lag_days: int) -> pd.DataFrame:
        if not isinstance(frame, pd.DataFrame):
            frame = pd.DataFrame(frame or [])
        if frame.empty:
            return pd.DataFrame(columns=STATEMENT_OBSERVATION_FIELDS)
        normalized = frame.copy()
        for column in STATEMENT_OBSERVATION_FIELDS:
            if column not in normalized.columns:
                normalized[column] = 0.0 if column not in {"Ticker", "Period_Type", "Statement_Date", "Availability_Date"} else ""
        normalized["Reporting_Lag_Days"] = normalized["Reporting_Lag_Days"].fillna(reporting_lag_days)
        return normalized[list(STATEMENT_OBSERVATION_FIELDS)]


@dataclass
class StockAnalysisHybridSource:
    metadata_dir: str = "data/processed/metadata"
    fallback_source: CachedYahooBundleSource = field(default_factory=CachedYahooBundleSource)
    now_factory: callable = datetime.now

    def fetch_ticker_bundle(self, ticker: str, reporting_lag_days: int = 45) -> Dict[str, object]:
        fallback_bundle = self.fallback_source.fetch_ticker_bundle(ticker, reporting_lag_days=reporting_lag_days)
        fallback_obs = fallback_bundle.get("observations")
        if not isinstance(fallback_obs, pd.DataFrame):
            fallback_obs = pd.DataFrame(columns=STATEMENT_OBSERVATION_FIELDS)

        stockanalysis_frame, scrape_path = self._load_stockanalysis_frame(ticker)
        quarterly, quarterly_provenance = self._build_quarterly_observations(
            ticker=ticker,
            stockanalysis_frame=stockanalysis_frame,
            fallback_observations=fallback_obs,
            reporting_lag_days=reporting_lag_days,
            scrape_path=scrape_path,
            fallback_source_id=fallback_bundle.get("source_id", YFINANCE_CACHE_SOURCE_ID),
            fallback_raw_path=fallback_bundle.get("raw_path"),
        )
        annual = fallback_obs.loc[fallback_obs["Period_Type"] == "annual"].copy()
        annual_provenance = self._build_fallback_provenance(
            annual,
            source_id=fallback_bundle.get("source_id", YFINANCE_CACHE_SOURCE_ID),
            raw_path=fallback_bundle.get("raw_path"),
        )

        observations = pd.concat([quarterly, annual], ignore_index=True, sort=False)
        if not observations.empty:
            observations = observations.sort_values(["Ticker", "Period_Type", "Statement_Date"]).reset_index(drop=True)
        else:
            observations = pd.DataFrame(columns=STATEMENT_OBSERVATION_FIELDS)

        provenance = pd.concat([quarterly_provenance, annual_provenance], ignore_index=True, sort=False)
        if not quarterly.empty:
            growth_rows = quarterly[["Ticker", "Statement_Date", "Revenue_Growth"]].copy()
            growth_rows["Period_Type"] = "quarterly"
            growth_rows["Item_Name"] = "Revenue_Growth"
            growth_rows["Value"] = growth_rows["Revenue_Growth"]
            growth_rows["Source"] = DERIVED_SOURCE_ID
            growth_rows["Source_File"] = ""
            growth_rows["Fallback_Reason"] = "computed_after_merge"
            provenance = pd.concat(
                [
                    provenance,
                    growth_rows[["Ticker", "Period_Type", "Statement_Date", "Item_Name", "Value", "Source", "Source_File", "Fallback_Reason"]],
                ],
                ignore_index=True,
                sort=False,
            )

        snapshot = self._build_snapshot(
            ticker=ticker,
            fallback_snapshot=fallback_bundle.get("snapshot"),
            quarterly=quarterly,
        )
        coverage = self._build_coverage_row(
            ticker=ticker,
            stockanalysis_frame=stockanalysis_frame,
            quarterly=quarterly,
            fallback_quarterly=fallback_obs.loc[fallback_obs["Period_Type"] == "quarterly"].copy(),
        )
        return {
            "snapshot": snapshot,
            "observations": observations,
            "provenance": provenance,
            "coverage": coverage,
        }

    def _load_stockanalysis_frame(self, ticker: str) -> Tuple[pd.DataFrame, Optional[str]]:
        symbol = ticker.replace(".BK", "")
        path = Path(self.metadata_dir) / f"stockanalysis_{symbol}.json"
        if not path.exists():
            return pd.DataFrame(columns=["quarter_label", *CORE_FIELD_MAP.values()]), None

        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("quarters", [])
        if not rows:
            return pd.DataFrame(columns=["quarter_label", *CORE_FIELD_MAP.values()]), str(path)

        frame = pd.DataFrame(rows)
        frame = frame.loc[frame["field"].isin(CORE_FIELD_MAP.keys())].copy()
        if frame.empty:
            return pd.DataFrame(columns=["quarter_label", *CORE_FIELD_MAP.values()]), str(path)

        frame["item_name"] = frame["field"].map(CORE_FIELD_MAP)
        pivot = (
            frame.pivot_table(index="quarter", columns="item_name", values="value", aggfunc="first")
            .reset_index()
            .rename(columns={"quarter": "quarter_label"})
        )
        for column in CORE_FIELD_MAP.values():
            if column not in pivot.columns:
                pivot[column] = pd.NA
        pivot["quarter_rank"] = pivot["quarter_label"].map(self._quarter_rank)
        pivot = pivot.dropna(subset=["quarter_rank"]).sort_values("quarter_rank").reset_index(drop=True)
        return pivot, str(path)

    def _build_quarterly_observations(
        self,
        *,
        ticker: str,
        stockanalysis_frame: pd.DataFrame,
        fallback_observations: pd.DataFrame,
        reporting_lag_days: int,
        scrape_path: Optional[str],
        fallback_source_id: str,
        fallback_raw_path: Optional[str],
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        fallback_quarterly = fallback_observations.loc[fallback_observations["Period_Type"] == "quarterly"].copy()
        fallback_quarterly = fallback_quarterly.sort_values("Statement_Date").reset_index(drop=True)
        if not fallback_quarterly.empty:
            fallback_quarterly["_source_id"] = fallback_source_id
            fallback_quarterly["_raw_path"] = fallback_raw_path or ""
        stock_by_date = self._map_stockanalysis_dates(stockanalysis_frame, fallback_quarterly)

        fallback_by_date = {
            str(row["Statement_Date"]): row
            for _, row in fallback_quarterly.iterrows()
        }
        union_dates = sorted(set(stock_by_date.keys()) | set(fallback_by_date.keys()))

        rows: List[Dict[str, object]] = []
        provenance_rows: List[Dict[str, object]] = []

        for statement_date in union_dates:
            stock_row = stock_by_date.get(statement_date, {})
            fallback_row = fallback_by_date.get(statement_date, {})

            row = {
                "Ticker": ticker,
                "Period_Type": "quarterly",
                "Statement_Date": statement_date,
                "Availability_Date": (
                    pd.Timestamp(statement_date) + pd.to_timedelta(reporting_lag_days, unit="D")
                ).date().isoformat(),
                "Reporting_Lag_Days": reporting_lag_days,
            }
            has_any_value = False
            for item_name in CORE_FIELD_MAP.values():
                value, source_id = self._pick_value(stock_row.get(item_name), fallback_row.get(item_name))
                row[item_name] = value
                has_any_value = has_any_value or pd.notna(value) and float(value) != 0.0
                provenance_rows.append(
                    {
                        "Ticker": ticker,
                        "Period_Type": "quarterly",
                        "Statement_Date": statement_date,
                        "Item_Name": item_name,
                        "Value": value,
                        "Source": source_id,
                        "Source_File": scrape_path if source_id == STOCKANALYSIS_SOURCE_ID else fallback_row.get("_raw_path", ""),
                        "Fallback_Reason": "" if source_id == STOCKANALYSIS_SOURCE_ID else "stockanalysis_missing_field_or_quarter",
                    }
                )

            for item_name in FALLBACK_ONLY_FIELDS:
                fallback_value = fallback_row.get(item_name, 0.0)
                row[item_name] = fallback_value if pd.notna(fallback_value) else 0.0
                has_any_value = has_any_value or (pd.notna(fallback_value) and float(fallback_value) != 0.0)
                provenance_rows.append(
                    {
                        "Ticker": ticker,
                        "Period_Type": "quarterly",
                        "Statement_Date": statement_date,
                        "Item_Name": item_name,
                        "Value": row[item_name],
                        "Source": fallback_row.get("_source_id", "missing") if pd.notna(fallback_value) else "missing",
                        "Source_File": fallback_row.get("_raw_path", ""),
                        "Fallback_Reason": "" if pd.notna(fallback_value) else "missing_in_all_sources",
                    }
                )

            row["Net_Debt"] = (row.get("Total_Debt") or 0.0) - (row.get("Total_Cash") or 0.0)
            if has_any_value:
                rows.append(row)

        if not rows:
            return pd.DataFrame(columns=STATEMENT_OBSERVATION_FIELDS), pd.DataFrame(
                columns=["Ticker", "Period_Type", "Statement_Date", "Item_Name", "Value", "Source", "Source_File", "Fallback_Reason"]
            )

        frame = pd.DataFrame(rows).sort_values("Statement_Date").reset_index(drop=True)
        frame["Revenue_Growth"] = frame["Revenue"].astype(float).replace({0.0: pd.NA}).pct_change()
        for column in STATEMENT_OBSERVATION_FIELDS:
            if column not in frame.columns:
                frame[column] = 0.0 if column not in {"Ticker", "Period_Type", "Statement_Date", "Availability_Date"} else ""
        provenance = pd.DataFrame(provenance_rows)
        return frame[list(STATEMENT_OBSERVATION_FIELDS)], provenance

    def _map_stockanalysis_dates(
        self,
        stockanalysis_frame: pd.DataFrame,
        fallback_quarterly: pd.DataFrame,
    ) -> Dict[str, Dict[str, object]]:
        if stockanalysis_frame.empty:
            return {}

        frame = stockanalysis_frame.copy()
        if not fallback_quarterly.empty:
            anchor_date = pd.Timestamp(fallback_quarterly["Statement_Date"].max())
            anchor_rank = int(frame["quarter_rank"].max())
            frame["Statement_Date"] = frame["quarter_rank"].apply(
                lambda rank: self._shift_quarter(anchor_date, anchor_rank - int(rank))
            )
        else:
            frame["Statement_Date"] = frame["quarter_label"].apply(self._calendar_quarter_end)

        frame["Statement_Date"] = pd.to_datetime(frame["Statement_Date"]).dt.date.astype(str)
        records = {}
        for _, row in frame.iterrows():
            records[str(row["Statement_Date"])] = row.to_dict()
        return records

    def _build_fallback_provenance(self, frame: pd.DataFrame, source_id: str, raw_path: Optional[str]) -> pd.DataFrame:
        rows: List[Dict[str, object]] = []
        if frame.empty:
            return pd.DataFrame(columns=["Ticker", "Period_Type", "Statement_Date", "Item_Name", "Value", "Source", "Source_File", "Fallback_Reason"])
        for _, observation in frame.iterrows():
            for item_name in (
                "Revenue",
                "EBIT",
                "FCF",
                "Total_Debt",
                "Total_Cash",
                "Net_Debt",
                "Shares_Issued",
                "Diluted_Average_Shares",
                "Revenue_Growth",
            ):
                rows.append(
                    {
                        "Ticker": observation["Ticker"],
                        "Period_Type": observation["Period_Type"],
                        "Statement_Date": observation["Statement_Date"],
                        "Item_Name": item_name,
                        "Value": observation.get(item_name, 0.0),
                        "Source": source_id,
                        "Source_File": raw_path or "",
                        "Fallback_Reason": "fallback_source_record",
                    }
                )
        return pd.DataFrame(rows)

    def _build_snapshot(
        self,
        *,
        ticker: str,
        fallback_snapshot: Optional[Dict[str, object]],
        quarterly: pd.DataFrame,
    ) -> Dict[str, object]:
        snapshot = self.fallback_source._normalize_snapshot(fallback_snapshot)
        snapshot["Ticker"] = ticker
        if not quarterly.empty:
            latest = quarterly.sort_values("Statement_Date").iloc[-1]
            for field in SNAPSHOT_OVERRIDE_FIELDS:
                value = latest.get(field)
                if pd.notna(value):
                    snapshot[field] = value
        if not snapshot.get("Fetched_Date"):
            snapshot["Fetched_Date"] = self.now_factory().strftime("%Y-%m-%d %H:%M:%S")
        return snapshot

    def _build_coverage_row(
        self,
        *,
        ticker: str,
        stockanalysis_frame: pd.DataFrame,
        quarterly: pd.DataFrame,
        fallback_quarterly: pd.DataFrame,
    ) -> Dict[str, object]:
        quarterly_dates = quarterly["Statement_Date"].tolist() if not quarterly.empty else []
        stock_fields = [column for column in CORE_FIELD_MAP.values() if column in stockanalysis_frame.columns]
        scraping_field_flags = {
            f"{field}_From_Scraping": bool(not stockanalysis_frame.empty and stockanalysis_frame[field].notna().any())
            for field in CORE_FIELD_MAP.values()
        }
        missing_scraping_fields = [field for field in CORE_FIELD_MAP.values() if not scraping_field_flags[f"{field}_From_Scraping"]]
        return {
            "Ticker": ticker,
            "StockAnalysis_File_Available": not stockanalysis_frame.empty,
            "StockAnalysis_Quarter_Count": int(len(stockanalysis_frame)),
            "Fallback_Quarter_Count": int(len(fallback_quarterly)),
            "Merged_Quarter_Count": int(len(quarterly)),
            "Quarterly_Start_Date": quarterly_dates[0] if quarterly_dates else "",
            "Quarterly_End_Date": quarterly_dates[-1] if quarterly_dates else "",
            "StockAnalysis_Core_Field_Count": int(
                sum(bool(stockanalysis_frame[field].notna().any()) for field in stock_fields)
            ),
            "Missing_Scraping_Fields": ",".join(missing_scraping_fields),
            **scraping_field_flags,
        }

    @staticmethod
    def _pick_value(stockanalysis_value: object, fallback_value: object) -> Tuple[float, str]:
        if pd.notna(stockanalysis_value):
            return float(stockanalysis_value), STOCKANALYSIS_SOURCE_ID
        if pd.notna(fallback_value):
            return float(fallback_value), YFINANCE_CACHE_SOURCE_ID
        return 0.0, "missing"

    @staticmethod
    def _quarter_rank(label: object) -> Optional[int]:
        if not isinstance(label, str):
            return None
        match = re.fullmatch(r"Q([1-4])\s+(\d{4})", label.strip())
        if not match:
            return None
        quarter = int(match.group(1))
        year = int(match.group(2))
        return year * 4 + quarter

    @staticmethod
    def _calendar_quarter_end(label: str) -> pd.Timestamp:
        match = re.fullmatch(r"Q([1-4])\s+(\d{4})", label.strip())
        if not match:
            raise ValueError(f"Unsupported quarter label: {label}")
        quarter = int(match.group(1))
        year = int(match.group(2))
        month = quarter * 3
        return pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)

    @staticmethod
    def _shift_quarter(anchor_date: pd.Timestamp, quarter_steps_back: int) -> pd.Timestamp:
        shifted = pd.Timestamp(anchor_date) - pd.DateOffset(months=3 * quarter_steps_back)
        return shifted + pd.offsets.MonthEnd(0)
