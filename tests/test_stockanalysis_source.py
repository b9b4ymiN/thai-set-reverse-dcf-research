import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from rdcf.data_sources.stockanalysis_source import (
    STOCKANALYSIS_SOURCE_ID,
    CachedYahooBundleSource,
    StockAnalysisHybridSource,
)


class StockAnalysisHybridSourceTests(unittest.TestCase):
    def test_scraping_values_extend_quarterly_history_and_keep_fallback_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            metadata_dir = root / "metadata"
            raw_root = root / "raw" / "set100" / "AOT.BK"
            metadata_dir.mkdir(parents=True, exist_ok=True)
            raw_root.mkdir(parents=True, exist_ok=True)

            stockanalysis_payload = {
                "symbol": "AOT",
                "quarters": [
                    {"quarter": "Q1 2026", "field": "revenue", "value": 16852.0, "raw_label": "Operating Revenue"},
                    {"quarter": "Q1 2026", "field": "ebit", "value": 6534.0, "raw_label": "Operating Income"},
                    {"quarter": "Q1 2026", "field": "free_cash_flow", "value": 4000.0, "raw_label": "Free Cash Flow"},
                    {"quarter": "Q4 2025", "field": "revenue", "value": 15766.0, "raw_label": "Operating Revenue"},
                    {"quarter": "Q4 2025", "field": "ebit", "value": 5522.0, "raw_label": "Operating Income"},
                    {"quarter": "Q4 2025", "field": "free_cash_flow", "value": 3500.0, "raw_label": "Free Cash Flow"},
                ],
            }
            (metadata_dir / "stockanalysis_AOT.json").write_text(json.dumps(stockanalysis_payload), encoding="utf-8")

            raw_payload = {
                "snapshot": {"Ticker": "AOT.BK", "Current_Price": 60.0, "Market_Cap": 1_000_000.0},
                "observations": [
                    {
                        "Ticker": "AOT.BK",
                        "Period_Type": "quarterly",
                        "Statement_Date": "2025-09-30",
                        "Availability_Date": "2025-11-14",
                        "Reporting_Lag_Days": 45,
                        "Revenue": 15_766.0,
                        "EBIT": 5_522.0,
                        "FCF": 3_500.0,
                        "Total_Debt": 100.0,
                        "Total_Cash": 40.0,
                        "Net_Debt": 60.0,
                        "Shares_Issued": 500.0,
                        "Diluted_Average_Shares": 510.0,
                        "Revenue_Growth": 0.0,
                    },
                    {
                        "Ticker": "AOT.BK",
                        "Period_Type": "quarterly",
                        "Statement_Date": "2025-12-31",
                        "Availability_Date": "2026-02-14",
                        "Reporting_Lag_Days": 45,
                        "Revenue": 16_852.0,
                        "EBIT": 6_534.0,
                        "FCF": 4_000.0,
                        "Total_Debt": 110.0,
                        "Total_Cash": 45.0,
                        "Net_Debt": 65.0,
                        "Shares_Issued": 520.0,
                        "Diluted_Average_Shares": 530.0,
                        "Revenue_Growth": 0.0,
                    },
                    {
                        "Ticker": "AOT.BK",
                        "Period_Type": "annual",
                        "Statement_Date": "2025-09-30",
                        "Availability_Date": "2025-11-14",
                        "Reporting_Lag_Days": 45,
                        "Revenue": 60_000.0,
                        "EBIT": 20_000.0,
                        "FCF": 10_000.0,
                        "Total_Debt": 110.0,
                        "Total_Cash": 45.0,
                        "Net_Debt": 65.0,
                        "Shares_Issued": 520.0,
                        "Diluted_Average_Shares": 530.0,
                        "Revenue_Growth": 0.0,
                    },
                ],
            }
            (raw_root / "fundamentals.json").write_text(json.dumps(raw_payload), encoding="utf-8")

            source = StockAnalysisHybridSource(
                metadata_dir=str(metadata_dir),
                fallback_source=CachedYahooBundleSource(raw_root=str(root / "raw" / "set100")),
            )
            bundle = source.fetch_ticker_bundle("AOT.BK")
            quarterly = bundle["observations"].loc[bundle["observations"]["Period_Type"] == "quarterly"].copy()

            self.assertEqual(quarterly["Statement_Date"].tolist(), ["2025-09-30", "2025-12-31"])
            self.assertEqual(float(quarterly.iloc[-1]["Revenue"]), 16852.0)
            self.assertEqual(float(quarterly.iloc[-1]["Total_Debt"]), 110.0)

            provenance = bundle["provenance"]
            revenue_source = provenance.loc[
                (provenance["Statement_Date"] == "2025-12-31") & (provenance["Item_Name"] == "Revenue"),
                "Source",
            ].iloc[0]
            debt_source = provenance.loc[
                (provenance["Statement_Date"] == "2025-12-31") & (provenance["Item_Name"] == "Total_Debt"),
                "Source",
            ].iloc[0]
            self.assertEqual(revenue_source, STOCKANALYSIS_SOURCE_ID)
            self.assertEqual(debt_source, "yahoo_yfinance_cached_raw")


if __name__ == "__main__":
    unittest.main()
