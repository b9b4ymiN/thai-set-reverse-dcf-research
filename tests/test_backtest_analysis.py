import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.pipeline.backtest_analysis import BacktestAnalysis


class BacktestAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        root = Path(self.tmpdir.name)
        self.snapshot_path = root / "snapshot.csv"
        self.portfolio_returns_path = root / "portfolio_returns.csv"
        self.summary_path = root / "summary.csv"
        self.holdings_dir = root

        pd.DataFrame([
            {"Ticker": "AAA.BK", "Sector": "Energy"},
            {"Ticker": "BBB.BK", "Sector": "Banking"},
        ]).to_csv(self.snapshot_path, index=False)

        pd.DataFrame([
            {"Ticker": "AAA.BK", "Horizon_Months": 3, "Forward_Return": 0.10, "Active_Return": 0.05},
            {"Ticker": "BBB.BK", "Horizon_Months": 3, "Forward_Return": 0.02, "Active_Return": -0.01},
            {"Ticker": "AAA.BK", "Horizon_Months": 6, "Forward_Return": 0.08, "Active_Return": 0.03},
        ]).to_csv(self.portfolio_returns_path, index=False)

        pd.DataFrame([
            {"Horizon_Months": 3, "Portfolio_Return": 0.06, "Benchmark_Return": 0.01, "Active_Return": 0.05, "Hit_Rate": 50.0, "Observations": 2},
            {"Horizon_Months": 6, "Portfolio_Return": 0.08, "Benchmark_Return": 0.05, "Active_Return": 0.03, "Hit_Rate": 100.0, "Observations": 1},
        ]).to_csv(self.summary_path, index=False)

        pd.DataFrame([
            {"Ticker": "AAA.BK", "Horizon_Months": 3, "Forward_Return": 0.10, "Active_Return": 0.05},
            {"Ticker": "BBB.BK", "Horizon_Months": 3, "Forward_Return": 0.02, "Active_Return": -0.01},
        ]).to_csv(root / "portfolio_2025-01-01_3m.csv", index=False)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_sector_summary_groups_by_sector_and_horizon(self):
        analysis = BacktestAnalysis(
            snapshot_path=str(self.snapshot_path),
            portfolio_returns_path=str(self.portfolio_returns_path),
            summary_path=str(self.summary_path),
            holdings_dir=str(self.holdings_dir),
        )
        sector = analysis.build_sector_summary()
        energy = sector[(sector["Sector"] == "Energy") & (sector["Horizon_Months"] == 3)].iloc[0]
        self.assertAlmostEqual(float(energy["Mean_Forward_Return"]), 0.10)
        self.assertEqual(int(energy["Selections"]), 1)

    def test_appendix_contains_both_sections(self):
        analysis = BacktestAnalysis(
            snapshot_path=str(self.snapshot_path),
            portfolio_returns_path=str(self.portfolio_returns_path),
            summary_path=str(self.summary_path),
            holdings_dir=str(self.holdings_dir),
        )
        appendix = analysis.build_appendix(
            analysis.build_sector_summary(),
            pd.DataFrame([{"WACC_Assumption": 0.08, "Horizon_Months": 3, "Active_Return": 0.05}]),
        )
        self.assertIn("## Sector Summary", appendix)
        self.assertIn("## WACC Sensitivity", appendix)


if __name__ == "__main__":
    unittest.main()
