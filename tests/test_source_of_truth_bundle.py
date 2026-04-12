import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.pipeline.source_of_truth_bundle import SourceOfTruthBundleBuilder


class FakeSource:
    def fetch_ticker_bundle(self, ticker, reporting_lag_days=45):
        snapshot = {
            "Ticker": ticker,
            "Company_Name": ticker,
            "Sector": "Utilities",
            "Industry": "Power",
            "Current_Price": 10.0,
            "Market_Cap": 100.0,
            "Revenue": 50.0,
            "Revenue_Growth": 0.1,
            "EBIT": 10.0,
            "FCF": 5.0,
            "Total_Debt": 20.0,
            "Total_Cash": 5.0,
            "WACC": 0.08,
            "Fetched_Date": "2026-04-12 00:00:00",
        }
        observations = pd.DataFrame(
            [
                {
                    "Ticker": ticker,
                    "Period_Type": "quarterly",
                    "Statement_Date": "2025-12-31",
                    "Availability_Date": "2026-02-14",
                    "Reporting_Lag_Days": reporting_lag_days,
                    "Revenue": 50.0,
                    "EBIT": 10.0,
                    "FCF": 5.0,
                    "Total_Debt": 20.0,
                    "Total_Cash": 5.0,
                    "Net_Debt": 15.0,
                    "Shares_Issued": 100.0,
                    "Diluted_Average_Shares": 100.0,
                    "Revenue_Growth": 0.1,
                }
            ]
        )
        provenance = pd.DataFrame(
            [
                {
                    "Ticker": ticker,
                    "Period_Type": "quarterly",
                    "Statement_Date": "2025-12-31",
                    "Item_Name": "Revenue",
                    "Value": 50.0,
                    "Source": "stockanalysis_scraping",
                    "Source_File": "fake.json",
                    "Fallback_Reason": "",
                }
            ]
        )
        coverage = {
            "Ticker": ticker,
            "StockAnalysis_File_Available": True,
            "StockAnalysis_Quarter_Count": 1,
            "Fallback_Quarter_Count": 0,
            "Merged_Quarter_Count": 1,
            "Quarterly_Start_Date": "2025-12-31",
            "Quarterly_End_Date": "2025-12-31",
            "StockAnalysis_Core_Field_Count": 3,
        }
        return {"snapshot": snapshot, "observations": observations, "provenance": provenance, "coverage": coverage}


class SourceOfTruthBundleBuilderTests(unittest.TestCase):
    def test_build_writes_bundle_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            raw_root = root / "raw" / "set100" / "AAA.BK"
            raw_root.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(
                [
                    {"Date": "2026-04-10", "Ticker": "AAA.BK", "Open": 1, "High": 1, "Low": 1, "Close": 1, "Adj Close": 1, "Volume": 100},
                ]
            ).to_csv(raw_root / "prices.csv", index=False)
            benchmark = root / "bench.csv"
            pd.DataFrame(
                [
                    {"Date": "2026-04-10", "Ticker": "^SET.BK", "Open": 1, "High": 1, "Low": 1, "Close": 1, "Adj Close": 1, "Volume": 100},
                ]
            ).to_csv(benchmark, index=False)

            builder = SourceOfTruthBundleBuilder(
                source=FakeSource(),
                raw_price_root=str(root / "raw" / "set100"),
                benchmark_price_path=str(benchmark),
            )
            manifest = builder.build(["AAA.BK"], output_dir=str(root / "bundle"))

            self.assertEqual(manifest["primary_source"], "stockanalysis_scraping")
            self.assertTrue((root / "bundle" / "fundamental_provenance.csv").exists())
            self.assertTrue((root / "bundle" / "fundamental_source_summary.csv").exists())
            self.assertTrue((root / "bundle" / "quarterly_source_coverage.csv").exists())

            summary = pd.read_csv(root / "bundle" / "fundamental_source_summary.csv")
            self.assertEqual(summary.iloc[0]["Source"], "stockanalysis_scraping")

            manifest_payload = json.loads((root / "bundle" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest_payload["coverage_summary"]["stockanalysis_ticker_count"], 1)


if __name__ == "__main__":
    unittest.main()
