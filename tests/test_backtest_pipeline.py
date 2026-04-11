import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.pipeline.backtest import ReverseDCFBacktester


def fake_signal_solver(**kwargs):
    price = kwargs["current_price"]
    fcf = kwargs["base_fcf"]
    shares = kwargs["shares_outstanding"]
    score = (fcf / shares / price) - 0.05
    intrinsic_value = price * (1 + score)
    return score, {
        "implied_growth": score,
        "intrinsic_value": intrinsic_value,
        "current_price": price,
        "premium_discount": (intrinsic_value / price) - 1,
        "converged": True,
    }


class ReverseDCFBacktesterTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        root = Path(self.tmpdir.name)

        snapshot = pd.DataFrame([
            {"Ticker": "AAA.BK", "WACC": 0.08},
            {"Ticker": "BBB.BK", "WACC": 0.09},
        ])
        observations = pd.DataFrame([
            {
                "Ticker": "AAA.BK",
                "Period_Type": "quarterly",
                "Statement_Date": "2024-09-30",
                "Availability_Date": "2024-11-14",
                "Reporting_Lag_Days": 45,
                "Revenue": 100.0,
                "EBIT": 20.0,
                "FCF": 12.0,
                "Total_Debt": 30.0,
                "Total_Cash": 5.0,
                "Net_Debt": 25.0,
                "Shares_Issued": 10.0,
                "Diluted_Average_Shares": 10.0,
                "Revenue_Growth": 0.10,
            },
            {
                "Ticker": "AAA.BK",
                "Period_Type": "quarterly",
                "Statement_Date": "2025-03-31",
                "Availability_Date": "2025-05-15",
                "Reporting_Lag_Days": 45,
                "Revenue": 150.0,
                "EBIT": 30.0,
                "FCF": 15.0,
                "Total_Debt": 30.0,
                "Total_Cash": 5.0,
                "Net_Debt": 25.0,
                "Shares_Issued": 10.0,
                "Diluted_Average_Shares": 10.0,
                "Revenue_Growth": 0.20,
            },
            {
                "Ticker": "BBB.BK",
                "Period_Type": "quarterly",
                "Statement_Date": "2024-09-30",
                "Availability_Date": "2024-11-14",
                "Reporting_Lag_Days": 45,
                "Revenue": 80.0,
                "EBIT": 10.0,
                "FCF": 8.0,
                "Total_Debt": 20.0,
                "Total_Cash": 3.0,
                "Net_Debt": 17.0,
                "Shares_Issued": 10.0,
                "Diluted_Average_Shares": 10.0,
                "Revenue_Growth": 0.05,
            },
        ])
        prices = pd.DataFrame([
            {"Date": "2025-01-02", "Ticker": "AAA.BK", "Open": 10, "High": 10, "Low": 10, "Close": 10, "Adj Close": 10, "Volume": 100},
            {"Date": "2025-04-01", "Ticker": "AAA.BK", "Open": 11, "High": 11, "Low": 11, "Close": 11, "Adj Close": 11, "Volume": 100},
            {"Date": "2025-07-01", "Ticker": "AAA.BK", "Open": 12, "High": 12, "Low": 12, "Close": 12, "Adj Close": 12, "Volume": 100},
            {"Date": "2025-01-02", "Ticker": "BBB.BK", "Open": 10, "High": 10, "Low": 10, "Close": 10, "Adj Close": 10, "Volume": 100},
            {"Date": "2025-04-01", "Ticker": "BBB.BK", "Open": 9, "High": 9, "Low": 9, "Close": 9, "Adj Close": 9, "Volume": 100},
            {"Date": "2025-07-01", "Ticker": "BBB.BK", "Open": 8, "High": 8, "Low": 8, "Close": 8, "Adj Close": 8, "Volume": 100},
        ])
        benchmark = pd.DataFrame([
            {"Date": "2025-01-02", "Ticker": "^SET.BK", "Open": 100, "High": 100, "Low": 100, "Close": 100, "Adj Close": 100, "Volume": 1000},
            {"Date": "2025-04-01", "Ticker": "^SET.BK", "Open": 102, "High": 102, "Low": 102, "Close": 102, "Adj Close": 102, "Volume": 1000},
            {"Date": "2025-07-01", "Ticker": "^SET.BK", "Open": 104, "High": 104, "Low": 104, "Close": 104, "Adj Close": 104, "Volume": 1000},
        ])

        self.snapshot_path = root / "snapshot.csv"
        self.observations_path = root / "observations.csv"
        self.prices_path = root / "prices.csv"
        self.benchmark_path = root / "benchmark.csv"
        snapshot.to_csv(self.snapshot_path, index=False)
        observations.to_csv(self.observations_path, index=False)
        prices.to_csv(self.prices_path, index=False)
        benchmark.to_csv(self.benchmark_path, index=False)

    def tearDown(self):
        self.tmpdir.cleanup()

    def build_backtester(self):
        return ReverseDCFBacktester(
            snapshot_path=str(self.snapshot_path),
            observations_path=str(self.observations_path),
            price_history_path=str(self.prices_path),
            benchmark_history_path=str(self.benchmark_path),
            signal_solver=fake_signal_solver,
        )

    def test_latest_available_observation_avoids_lookahead(self):
        backtester = self.build_backtester()
        observation = backtester._latest_available_observation("AAA.BK", pd.Timestamp("2025-04-01"))
        self.assertEqual(observation["Statement_Date"].date().isoformat(), "2024-09-30")

    def test_forward_return_uses_target_horizon(self):
        backtester = self.build_backtester()
        portfolio = pd.DataFrame([{
            "Ticker": "AAA.BK",
            "Price": 10.0,
            "Signal_Score": 0.1,
        }])
        holdings, benchmark_return = backtester._evaluate_portfolio_horizon(portfolio, pd.Timestamp("2025-01-02"), 3)
        self.assertAlmostEqual(float(holdings.iloc[0]["Forward_Return"]), 0.1)
        self.assertAlmostEqual(float(benchmark_return), 0.02)

    def test_run_produces_summary_and_manifest(self):
        backtester = self.build_backtester()
        with tempfile.TemporaryDirectory() as outdir:
            result = backtester.run(
                output_dir=outdir,
                horizons=[3],
                top_n=1,
                rebalance_frequency="QS",
                start_date="2025-01-01",
                end_date="2025-01-31",
            )
            self.assertGreater(result["signals"], 0)
            self.assertTrue((Path(outdir) / "summary.csv").exists())
            self.assertTrue((Path(outdir) / "exclusions.csv").exists())
            self.assertTrue((Path(outdir) / "audit_sample.csv").exists())
            self.assertTrue((Path(outdir) / "no_lookahead_audit.md").exists())
            summary = pd.read_csv(Path(outdir) / "summary.csv")
            self.assertEqual(summary.iloc[0]["Horizon_Months"], 3)
            self.assertIn("Avg_Turnover", summary.columns)
            manifest = pd.read_json(Path(outdir) / "manifest.json", typ="series")
            self.assertEqual(manifest["no_lookahead_failures"], 0)
            self.assertEqual(manifest["wacc_mode"], "fixed")


if __name__ == "__main__":
    unittest.main()
