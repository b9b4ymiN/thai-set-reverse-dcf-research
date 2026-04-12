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
        self.root = Path(self.tmpdir.name)
        self.snapshot_path = self.root / "snapshot.csv"
        self.observations_path = self.root / "observations.csv"
        self.prices_path = self.root / "prices.csv"
        self.benchmark_path = self.root / "benchmark.csv"
        self._write_base_fixture()

    def tearDown(self):
        self.tmpdir.cleanup()

    def _write_dataset(self, snapshot: pd.DataFrame, observations: pd.DataFrame, prices: pd.DataFrame, benchmark: pd.DataFrame):
        snapshot.to_csv(self.snapshot_path, index=False)
        observations.to_csv(self.observations_path, index=False)
        prices.to_csv(self.prices_path, index=False)
        benchmark.to_csv(self.benchmark_path, index=False)

    def _write_base_fixture(self):
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
            {"Date": "2025-02-15", "Ticker": "AAA.BK", "Open": 9.5, "High": 9.5, "Low": 9.5, "Close": 9.5, "Adj Close": 9.5, "Volume": 100},
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
        self._write_dataset(snapshot, observations, prices, benchmark)

    def _write_buy_ban_fixture(self):
        snapshot = pd.DataFrame([
            {"Ticker": "AAA.BK", "WACC": 0.08},
            {"Ticker": "BBB.BK", "WACC": 0.09},
        ])
        observations = pd.DataFrame([
            {
                "Ticker": ticker,
                "Period_Type": "quarterly",
                "Statement_Date": statement_date,
                "Availability_Date": availability_date,
                "Reporting_Lag_Days": 45,
                "Revenue": revenue,
                "EBIT": revenue * 0.2,
                "FCF": fcf,
                "Total_Debt": 10.0,
                "Total_Cash": 2.0,
                "Net_Debt": 8.0,
                "Shares_Issued": 10.0,
                "Diluted_Average_Shares": 10.0,
                "Revenue_Growth": revenue_growth,
            }
            for ticker, revenue_growth, fcf, revenue in [
                ("AAA.BK", 0.18, 12.0, 120.0),
                ("BBB.BK", 0.06, 8.0, 80.0),
            ]
            for statement_date, availability_date in [
                ("2024-09-30", "2024-11-14"),
                ("2024-12-31", "2025-02-14"),
                ("2025-03-31", "2025-05-15"),
                ("2025-06-30", "2025-08-14"),
            ]
        ])
        prices = pd.DataFrame([
            {"Date": "2025-01-02", "Ticker": "AAA.BK", "Open": 10, "High": 10, "Low": 10, "Close": 10, "Adj Close": 10, "Volume": 100},
            {"Date": "2025-04-01", "Ticker": "AAA.BK", "Open": 9, "High": 9, "Low": 9, "Close": 9, "Adj Close": 9, "Volume": 100},
            {"Date": "2025-07-01", "Ticker": "AAA.BK", "Open": 8, "High": 8, "Low": 8, "Close": 8, "Adj Close": 8, "Volume": 100},
            {"Date": "2025-10-01", "Ticker": "AAA.BK", "Open": 7, "High": 7, "Low": 7, "Close": 7, "Adj Close": 7, "Volume": 100},
            {"Date": "2025-01-02", "Ticker": "BBB.BK", "Open": 10, "High": 10, "Low": 10, "Close": 10, "Adj Close": 10, "Volume": 100},
            {"Date": "2025-04-01", "Ticker": "BBB.BK", "Open": 10.5, "High": 10.5, "Low": 10.5, "Close": 10.5, "Adj Close": 10.5, "Volume": 100},
            {"Date": "2025-07-01", "Ticker": "BBB.BK", "Open": 11, "High": 11, "Low": 11, "Close": 11, "Adj Close": 11, "Volume": 100},
            {"Date": "2025-10-01", "Ticker": "BBB.BK", "Open": 11.5, "High": 11.5, "Low": 11.5, "Close": 11.5, "Adj Close": 11.5, "Volume": 100},
        ])
        benchmark = pd.DataFrame([
            {"Date": "2025-01-02", "Ticker": "^SET.BK", "Open": 100, "High": 100, "Low": 100, "Close": 100, "Adj Close": 100, "Volume": 1000},
            {"Date": "2025-04-01", "Ticker": "^SET.BK", "Open": 101, "High": 101, "Low": 101, "Close": 101, "Adj Close": 101, "Volume": 1000},
            {"Date": "2025-07-01", "Ticker": "^SET.BK", "Open": 102, "High": 102, "Low": 102, "Close": 102, "Adj Close": 102, "Volume": 1000},
            {"Date": "2025-10-01", "Ticker": "^SET.BK", "Open": 103, "High": 103, "Low": 103, "Close": 103, "Adj Close": 103, "Volume": 1000},
        ])
        self._write_dataset(snapshot, observations, prices, benchmark)

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
        self.assertEqual(holdings.iloc[0]["Exit_Reason"], "horizon_end")

    def test_risk_control_case_uses_daily_stop_loss(self):
        backtester = self.build_backtester()
        with tempfile.TemporaryDirectory() as outdir:
            backtester.run(
                output_dir=outdir,
                horizons=[3],
                top_n=1,
                rebalance_frequency="QS",
                start_date="2025-01-01",
                end_date="2025-01-31",
                case_name="risk_control",
                stop_loss_pct=0.05,
            )
            holdings = pd.read_csv(Path(outdir) / "portfolio_2025-01-02_3m.csv")
            self.assertEqual(holdings.iloc[0]["Exit_Reason"], "stop_loss")
            self.assertEqual(holdings.iloc[0]["End_Date"], "2025-02-15")
            self.assertAlmostEqual(float(holdings.iloc[0]["Forward_Return"]), -0.05)

    def test_run_produces_summary_manifest_and_trade_logs(self):
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
            self.assertTrue((Path(outdir) / "trade_log.csv").exists())
            self.assertTrue((Path(outdir) / "buy_ban_ledger.csv").exists())
            self.assertTrue((Path(outdir) / "no_lookahead_audit.md").exists())
            summary = pd.read_csv(Path(outdir) / "summary.csv")
            self.assertEqual(summary.iloc[0]["Horizon_Months"], 3)
            self.assertEqual(summary.iloc[0]["Case_Name"], "baseline")
            self.assertIn("Avg_Turnover", summary.columns)
            manifest = pd.read_json(Path(outdir) / "manifest.json", typ="series")
            self.assertEqual(manifest["no_lookahead_failures"], 0)
            self.assertEqual(manifest["wacc_mode"], "fixed")
            self.assertFalse(manifest["daily_stop_loss_enabled"])

    def test_buy_ban_excludes_ticker_after_third_losing_round(self):
        self._write_buy_ban_fixture()
        backtester = self.build_backtester()
        with tempfile.TemporaryDirectory() as outdir:
            backtester.run(
                output_dir=outdir,
                horizons=[3],
                top_n=1,
                rebalance_frequency="QS",
                start_date="2025-01-01",
                end_date="2025-10-31",
                case_name="baseline",
            )
            exclusions = pd.read_csv(Path(outdir) / "exclusions.csv")
            banned_row = exclusions[
                (exclusions["Ticker"] == "AAA.BK") &
                (exclusions["Rebalance_Date"] == "2025-10-01") &
                (exclusions["Exclusion_Reason"] == "buy_ban_active")
            ]
            self.assertEqual(len(banned_row), 1)
            trade_log = pd.read_csv(Path(outdir) / "trade_log.csv")
            aaa_rounds = trade_log[trade_log["Ticker"] == "AAA.BK"]
            self.assertEqual(len(aaa_rounds), 3)
            self.assertEqual(int(aaa_rounds.iloc[-1]["Losing_Buy_Rounds"]), 3)
            self.assertTrue(bool(aaa_rounds.iloc[-1]["Buy_Ban_Triggered"]))
            buy_ban_ledger = pd.read_csv(Path(outdir) / "buy_ban_ledger.csv")
            self.assertEqual(len(buy_ban_ledger), 1)
            self.assertEqual(buy_ban_ledger.iloc[0]["Ticker"], "AAA.BK")

    def test_run_case_matrix_generates_all_baseline_and_risk_control_cases(self):
        backtester = self.build_backtester()
        with tempfile.TemporaryDirectory() as outdir:
            result = backtester.run_case_matrix(
                output_root=outdir,
                horizons=[3],
                top_n_values=[5, 10],
                rebalance_frequency="QS",
                start_date="2025-01-01",
                end_date="2025-01-31",
                risk_control_stop_losses=[0.05, 0.10],
            )
            self.assertEqual(result["case_count"], 6)
            comparison = pd.read_csv(Path(outdir) / "comparison_summary.csv")
            self.assertEqual(set(comparison["Case_Name"]), {"baseline", "risk_control"})
            self.assertEqual(set(comparison["Top_N"]), {5, 10})
            self.assertEqual(set(comparison["Stop_Loss_Pct"]), {0.0, 0.05, 0.10})

    def test_run_includes_damodaran_methodology_in_outputs(self):
        backtester = self.build_backtester()
        with tempfile.TemporaryDirectory() as outdir:
            backtester.run(output_dir=outdir)
            manifest = pd.read_json(Path(outdir) / "manifest.json", typ="series")
            self.assertEqual(manifest["methodology"], "Damodaran Stern Reverse DCF")
            self.assertIn("https://pages.stern.nyu.edu", manifest["framework_reference"])

            report_content = (Path(outdir) / "report.md").read_text()
            self.assertIn("Damodaran Stern Reverse DCF framework", report_content)
            self.assertIn("METHODOLOGY.md", report_content)


class SourceOfTruth100IntegrationTests(unittest.TestCase):
    def test_100_stock_universe_size(self):
        backtester = ReverseDCFBacktester()
        self.assertEqual(len(backtester.universe_tickers), 100)

    def test_scraping_first_source_priority(self):
        provenance_path = Path("research_data/source_of_truth_100/fundamental_provenance.csv")
        self.assertTrue(provenance_path.exists())
        df = pd.read_csv(provenance_path)
        core_fields = {"Revenue", "EBIT", "FCF"}
        sa_provenance = df[df["Source"] == "stockanalysis_scraping"]
        sa_fields = set(sa_provenance["Item_Name"].unique())
        self.assertTrue(core_fields.issubset(sa_fields), f"StockAnalysis should cover {core_fields}, but only found {sa_fields}")


if __name__ == "__main__":
    unittest.main()
