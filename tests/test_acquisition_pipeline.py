import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.pipeline.acquisition import AcquisitionPipeline


class FakeSource:
    def fetch_ticker_bundle(self, ticker, reporting_lag_days=45):
        observations = pd.DataFrame(
            [
                {
                    "Ticker": "AAA.BK",
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
                },
                {
                    "Ticker": "AAA.BK",
                    "Period_Type": "annual",
                    "Statement_Date": "2025-12-31",
                    "Availability_Date": "2026-02-14",
                    "Reporting_Lag_Days": reporting_lag_days,
                    "Revenue": 200.0,
                    "EBIT": 40.0,
                    "FCF": 20.0,
                    "Total_Debt": 20.0,
                    "Total_Cash": 5.0,
                    "Net_Debt": 15.0,
                    "Shares_Issued": 100.0,
                    "Diluted_Average_Shares": 100.0,
                    "Revenue_Growth": 0.15,
                },
            ]
        )
        snapshot = {
            "Ticker": "AAA.BK",
            "Company_Name": "AAA",
            "Sector": "Finance",
            "Industry": "Banks",
            "Current_Price": 10.0,
            "Market_Cap": 100.0,
            "EPS": 2.0,
            "PE_Ratio": 5.0,
            "PB_Ratio": 1.0,
            "EV_EBITDA": 4.0,
            "Revenue": 50.0,
            "Revenue_Growth": 0.1,
            "EBIT": 10.0,
            "FCF": 5.0,
            "Total_Debt": 20.0,
            "Total_Cash": 5.0,
            "Debt_to_Equity": 0.5,
            "Current_Ratio": 1.2,
            "Profit_Margin": 0.2,
            "Operating_Margin": 0.15,
            "ROE": 0.12,
            "ROA": 0.05,
            "Beta": 1.1,
            "Cost_of_Equity": 0.08,
            "Cost_of_Debt": 0.04,
            "WACC": 0.07,
            "Dividend_Yield": 0.02,
            "Payout_Ratio": 0.4,
            "Earnings_Growth": 0.11,
            "Fetched_Date": "2026-04-11 03:00:00",
        }
        if ticker == "AAA.BK":
            return {"snapshot": snapshot, "observations": observations}
        return {"snapshot": None, "observations": pd.DataFrame(columns=observations.columns)}


def fake_download(*, tickers, **_kwargs):
    idx = pd.to_datetime(["2026-04-10", "2026-04-11"])
    if len(tickers) == 1:
        return pd.DataFrame(
            {
                "Open": [10.0, 10.5],
                "High": [10.2, 10.7],
                "Low": [9.8, 10.2],
                "Close": [10.1, 10.6],
                "Adj Close": [10.1, 10.6],
                "Volume": [1000, 1200],
            },
            index=idx,
        )
    columns = pd.MultiIndex.from_product(
        [tickers, ["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
    )
    data = [
        [10.0, 10.2, 9.8, 10.1, 10.1, 1000, 20.0, 20.2, 19.8, 20.1, 20.1, 2000],
        [10.5, 10.7, 10.2, 10.6, 10.6, 1200, 20.5, 20.7, 20.2, 20.6, 20.6, 2200],
    ]
    return pd.DataFrame(data, index=idx, columns=columns)


class AcquisitionPipelineTests(unittest.TestCase):
    def test_run_writes_raw_processed_and_metadata_outputs(self):
        pipeline = AcquisitionPipeline(
            source=FakeSource(),
            history_downloader=fake_download,
            benchmark_ticker="^SET.BK",
            reporting_lag_days=45,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = pipeline.run(["AAA.BK", "BBB.BK"], output_root=tmpdir, period="1y")

            raw_fundamentals = Path(tmpdir) / "raw" / "set100" / "AAA.BK" / "fundamentals.json"
            raw_prices = Path(tmpdir) / "raw" / "set100" / "AAA.BK" / "prices.csv"
            quarterly = Path(tmpdir) / "processed" / "fundamentals" / "quarterly" / "fundamentals.parquet"
            annual = Path(tmpdir) / "processed" / "fundamentals" / "annual" / "fundamentals.parquet"
            prices = Path(tmpdir) / "processed" / "prices" / "daily" / "prices.parquet"
            manifest_path = Path(tmpdir) / "processed" / "metadata" / "data_manifest.json"
            log_path = Path(tmpdir) / "processed" / "metadata" / "acquisition_log.json"

            self.assertTrue(raw_fundamentals.exists())
            self.assertTrue(raw_prices.exists())
            self.assertTrue(quarterly.exists())
            self.assertTrue(annual.exists())
            self.assertTrue(prices.exists())
            self.assertTrue(manifest_path.exists())
            self.assertTrue(log_path.exists())

            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest_payload["primary_source"], "yahoo_yfinance")
            self.assertEqual(manifest_payload["source_review"]["chosen_source"]["id"], "yahoo_yfinance")
            self.assertCountEqual(
                [item["id"] for item in manifest_payload["source_review"]["alternatives"]],
                ["set_website_scraping", "investing_com_scraping", "smartxl_trial"],
            )
            self.assertEqual(manifest_payload["quality_summary"]["missing_fundamental_tickers"], ["BBB.BK"])
            self.assertEqual(manifest_payload["quality_summary"]["missing_price_tickers"], [])
            self.assertTrue(any(item["label"] == "processed_quarterly_fundamentals" for item in manifest_payload["files"]))

            quarterly_df = pd.read_parquet(quarterly)
            annual_df = pd.read_parquet(annual)
            prices_df = pd.read_parquet(prices)
            self.assertEqual(set(quarterly_df["period_type"]), {"quarterly"})
            self.assertEqual(set(annual_df["period_type"]), {"annual"})
            self.assertIn("is_benchmark", prices_df.columns)
            self.assertTrue(prices_df["is_benchmark"].any())

            raw_payload = json.loads(raw_fundamentals.read_text(encoding="utf-8"))
            self.assertEqual(raw_payload["source"], "yahoo_yfinance")
            self.assertEqual(raw_payload["validation_reference"]["SET_Symbol"], "AAA")

            log_payload = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(log_payload[-1]["run_id"], manifest["run_id"])


if __name__ == "__main__":
    unittest.main()
