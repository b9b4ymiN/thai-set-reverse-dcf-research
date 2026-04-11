import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.pipeline.backtest_visuals import BacktestVisualizer


class BacktestVisualizerTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        root = Path(self.tmpdir.name)
        self.summary = root / "summary.csv"
        self.sector = root / "sector.csv"
        self.sensitivity = root / "sensitivity.csv"

        pd.DataFrame([
            {"Horizon_Months": 3, "Active_Return": 0.01, "Hit_Rate": 55.0},
            {"Horizon_Months": 6, "Active_Return": 0.02, "Hit_Rate": 65.0},
        ]).to_csv(self.summary, index=False)
        pd.DataFrame([
            {"Sector": "Energy", "Horizon_Months": 3, "Mean_Active_Return": 0.01},
            {"Sector": "Energy", "Horizon_Months": 6, "Mean_Active_Return": 0.02},
            {"Sector": "Banking", "Horizon_Months": 3, "Mean_Active_Return": -0.01},
            {"Sector": "Banking", "Horizon_Months": 6, "Mean_Active_Return": 0.00},
        ]).to_csv(self.sector, index=False)
        pd.DataFrame([
            {"WACC_Assumption": 0.06, "Horizon_Months": 3, "Active_Return": 0.01},
            {"WACC_Assumption": 0.08, "Horizon_Months": 3, "Active_Return": 0.02},
            {"WACC_Assumption": 0.06, "Horizon_Months": 6, "Active_Return": 0.015},
            {"WACC_Assumption": 0.08, "Horizon_Months": 6, "Active_Return": 0.025},
        ]).to_csv(self.sensitivity, index=False)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_generate_writes_all_expected_figures(self):
        visualizer = BacktestVisualizer(
            summary_path=str(self.summary),
            sector_summary_path=str(self.sector),
            sensitivity_path=str(self.sensitivity),
        )
        outdir = Path(self.tmpdir.name) / "figures"
        manifest = visualizer.generate(output_dir=str(outdir))
        for path in manifest.values():
            self.assertTrue(Path(path).exists())
        self.assertTrue((outdir / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
