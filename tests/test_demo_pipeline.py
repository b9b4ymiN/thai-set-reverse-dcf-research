import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.pipeline.demo import BacktestDemoRunner


class BacktestDemoRunnerTests(unittest.TestCase):
    def test_demo_run_writes_dataset_backtest_and_bundle_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / 'demo'
            manifest = BacktestDemoRunner().run(output_dir=str(output_dir), include_bundle=True)

            self.assertTrue((output_dir / 'dataset' / 'fundamentals_snapshot.csv').exists())
            self.assertTrue((output_dir / 'dataset' / 'fundamental_observations.csv').exists())
            self.assertTrue((output_dir / 'backtest' / 'summary.csv').exists())
            self.assertTrue((output_dir / 'backtest' / 'appendix.md').exists())
            self.assertTrue((output_dir / 'backtest' / 'figures' / 'manifest.json').exists())
            self.assertTrue((output_dir / 'bundle' / 'README.md').exists())
            self.assertTrue((output_dir / 'demo_manifest.json').exists())

            summary = pd.read_csv(output_dir / 'backtest' / 'summary.csv')
            self.assertEqual(sorted(summary['Horizon_Months'].tolist()), [3, 6, 12])
            self.assertGreater(manifest['backtest']['signals'], 0)
            self.assertEqual(manifest['analysis']['wacc_sensitivity_rows'], 9)


if __name__ == '__main__':
    unittest.main()
