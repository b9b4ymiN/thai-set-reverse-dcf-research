import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import pandas as pd

from rdcf.data_pipeline import ResearchDataPipeline
from rdcf.data_sources.yahoo_source import YahooFinanceSource


class ResearchDataPipelineTests(unittest.TestCase):
    def setUp(self):
        self.source = YahooFinanceSource(
            ticker_factory=lambda ticker: None,
            now_factory=lambda: datetime(2026, 4, 11, 3, 0, 0),
        )
        snapshot = {
            'Ticker': 'AAA.BK',
            'Company_Name': 'AAA',
            'Sector': 'Finance',
            'Industry': 'Banks',
            'Current_Price': 10.0,
            'Market_Cap': 100.0,
            'EPS': 2.0,
            'PE_Ratio': 5.0,
            'PB_Ratio': 1.0,
            'EV_EBITDA': 4.0,
            'Revenue': 50.0,
            'Revenue_Growth': 0.1,
            'EBIT': 10.0,
            'FCF': 5.0,
            'Total_Debt': 20.0,
            'Total_Cash': 5.0,
            'Debt_to_Equity': 0.5,
            'Current_Ratio': 1.2,
            'Profit_Margin': 0.2,
            'Operating_Margin': 0.15,
            'ROE': 0.12,
            'ROA': 0.05,
            'Beta': 1.1,
            'Cost_of_Equity': 0.08,
            'Cost_of_Debt': 0.04,
            'WACC': 0.07,
            'Dividend_Yield': 0.02,
            'Payout_Ratio': 0.4,
            'Earnings_Growth': 0.11,
            'Fetched_Date': '2026-04-11 03:00:00',
        }
        observations = pd.DataFrame([
            {
                'Ticker': 'AAA.BK',
                'Period_Type': 'quarterly',
                'Statement_Date': '2025-12-31',
                'Availability_Date': '2026-02-14',
                'Reporting_Lag_Days': 45,
                'Revenue': 50.0,
                'EBIT': 10.0,
                'FCF': 5.0,
                'Total_Debt': 20.0,
                'Total_Cash': 5.0,
                'Net_Debt': 15.0,
                'Shares_Issued': 100.0,
                'Diluted_Average_Shares': 100.0,
                'Revenue_Growth': 0.1,
            }
        ])
        self.source.fetch_ticker_bundle = lambda ticker, reporting_lag_days=45: {
            'snapshot': snapshot if ticker == 'AAA.BK' else None,
            'observations': observations if ticker == 'AAA.BK' else pd.DataFrame(columns=observations.columns),
        }

        def fake_download(*, tickers, **_kwargs):
            idx = pd.to_datetime(['2026-04-10', '2026-04-11'])
            if len(tickers) == 1:
                return pd.DataFrame({
                    'Open': [10.0, 10.5],
                    'High': [10.2, 10.7],
                    'Low': [9.8, 10.2],
                    'Close': [10.1, 10.6],
                    'Adj Close': [10.1, 10.6],
                    'Volume': [1000, 1200],
                }, index=idx)
            columns = pd.MultiIndex.from_product([
                tickers,
                ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'],
            ])
            data = [
                [10.0, 10.2, 9.8, 10.1, 10.1, 1000, 20.0, 20.2, 19.8, 20.1, 20.1, 2000],
                [10.5, 10.7, 10.2, 10.6, 10.6, 1200, 20.5, 20.7, 20.2, 20.6, 20.6, 2200],
            ]
            return pd.DataFrame(data, index=idx, columns=columns)

        self.pipeline = ResearchDataPipeline(
            source=self.source,
            history_downloader=fake_download,
            benchmark_ticker='^SET.BK',
            reporting_lag_days=45,
        )

    def test_build_fundamental_observations_adds_dates(self):
        observations = self.pipeline.build_fundamental_observations([self.source.fetch_ticker_bundle('AAA.BK')])
        self.assertEqual(observations.iloc[0]['Statement_Date'], '2025-12-31')
        self.assertEqual(observations.iloc[0]['Availability_Date'], '2026-02-14')
        self.assertEqual(observations.iloc[0]['Reporting_Lag_Days'], 45)

    def test_build_research_dataset_writes_bundle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = self.pipeline.build_research_dataset(['AAA.BK', 'BBB.BK'], output_dir=tmpdir, period='1y')
            self.assertEqual(manifest['benchmark_ticker'], '^SET.BK')
            self.assertEqual(manifest['rows']['fundamentals'], 1)
            self.assertEqual(manifest['rows']['observations'], 1)
            self.assertTrue(Path(manifest['paths']['manifest']).exists())
            self.assertTrue(Path(manifest['paths']['prices']).exists())
            self.assertTrue(Path(manifest['paths']['benchmark']).exists())
            self.assertTrue(Path(manifest['paths']['price_coverage']).exists())
            self.assertEqual(manifest['missing_price_tickers'], [])
            self.assertEqual(manifest['missing_fundamental_tickers'], ['BBB.BK'])

    def test_normalize_price_history_handles_single_ticker_frame(self):
        idx = pd.to_datetime(['2026-04-10'])
        raw = pd.DataFrame({'Open': [10.0], 'High': [10.2], 'Low': [9.8], 'Close': [10.1], 'Adj Close': [10.1], 'Volume': [1000]}, index=idx)
        history = self.pipeline._normalize_price_history(raw, ['AAA.BK'])
        self.assertEqual(history.iloc[0]['Ticker'], 'AAA.BK')
        self.assertEqual(history.iloc[0]['Date'], '2026-04-10')

    def test_build_price_coverage_report_marks_missing_tickers(self):
        history = pd.DataFrame([
            {'Date': '2026-04-10', 'Ticker': 'AAA.BK', 'Open': 1, 'High': 1, 'Low': 1, 'Close': 1, 'Adj Close': 1, 'Volume': 1},
        ])
        coverage = self.pipeline.build_price_coverage_report(['AAA.BK', 'BBB.BK', 'AAA.BK'], history)
        self.assertEqual(coverage['Ticker'].tolist(), ['AAA.BK', 'BBB.BK'])
        self.assertEqual(coverage.loc[coverage['Ticker'] == 'BBB.BK', 'Price_Row_Count'].iloc[0], 0)

    def test_normalize_price_history_drops_all_nan_price_rows(self):
        idx = pd.to_datetime(['2026-04-10'])
        columns = pd.MultiIndex.from_product([
            ['AAA.BK', 'BBB.BK'],
            ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'],
        ])
        raw = pd.DataFrame([[1, 1, 1, 1, 1, 1, None, None, None, None, None, None]], index=idx, columns=columns)
        history = self.pipeline._normalize_price_history(raw, ['AAA.BK', 'BBB.BK'])
        self.assertEqual(history['Ticker'].tolist(), ['AAA.BK'])


if __name__ == '__main__':
    unittest.main()
