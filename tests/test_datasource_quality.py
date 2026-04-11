import unittest

import pandas as pd

from rdcf.data_sources.set_site_validation import build_validation_reference
from rdcf.data_sources.yahoo_source import build_datasource_quality_report, build_reverse_dcf_exclusion_report


class DatasourceQualityTests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame([
            {'Ticker': 'AAA.BK', 'Current_Price': 10.0, 'Market_Cap': 100.0, 'FCF': 5.0, 'WACC': 0.1, 'Revenue': 50.0},
            {'Ticker': 'BBB.BK', 'Current_Price': 0.0, 'Market_Cap': 80.0, 'FCF': 0.0, 'WACC': 0.0, 'Revenue': 0.0},
        ])

    def test_quality_report_marks_required_fields(self):
        report = build_datasource_quality_report(self.df)
        required = report[report['Field'] == 'Current_Price'].iloc[0]
        self.assertTrue(required['Required_For_Reverse_DCF'])
        self.assertEqual(required['Zero_Count'], 1)

    def test_exclusion_report_lists_failed_requirements(self):
        report = build_reverse_dcf_exclusion_report(self.df)
        failed = report[report['Ticker'] == 'BBB.BK'].iloc[0]
        self.assertFalse(failed['Passes_Reverse_DCF_Filter'])
        self.assertIn('Current_Price<=0_or_missing', failed['Exclusion_Reasons'])
        self.assertIn('FCF<=0_or_missing', failed['Exclusion_Reasons'])

    def test_set_validation_reference_uses_set_urls(self):
        ref = build_validation_reference('ptt.bk')
        self.assertEqual(ref['SET_Symbol'], 'PTT')
        self.assertIn('/quote/PTT/price', ref['SET_Price_URL'])
        self.assertIn('/quote/PTT/factsheet', ref['SET_Factsheet_URL'])


if __name__ == '__main__':
    unittest.main()
