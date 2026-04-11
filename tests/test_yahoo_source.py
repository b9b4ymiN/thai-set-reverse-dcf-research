import unittest
from datetime import datetime
from types import SimpleNamespace

import pandas as pd

from rdcf.data_sources.yahoo_source import YahooFinanceSource


class YahooSourceTests(unittest.TestCase):
    def test_fetch_stock_data_normalizes_expected_fields(self):
        cash_flow = pd.DataFrame({0: [120.0, -20.0]}, index=['Operating Cash Flow', 'Capital Expenditure'])
        income_stmt = pd.DataFrame({0: [1000.0, 50.0]}, index=['Total Revenue', 'Interest Expense'])
        stock = SimpleNamespace(
            info={
                'currentPrice': 10.0,
                'marketCap': 1000.0,
                'trailingEps': 2.0,
                'trailingPE': 5.0,
                'priceToBook': 1.2,
                'enterpriseToEbitda': 6.0,
                'totalDebt': 100.0,
                'totalCash': 40.0,
                'debtToEquity': 0.4,
                'currentRatio': 1.3,
                'profitMargins': 0.2,
                'operatingMargins': 0.15,
                'returnOnEquity': 0.18,
                'returnOnAssets': 0.1,
                'revenueGrowth': 0.08,
                'earningsGrowth': 0.11,
                'dividendYield': 0.03,
                'payoutRatio': 0.5,
                'beta': 1.1,
                'longName': 'Example Public Co',
                'sector': 'Utilities',
                'industry': 'Power',
            },
            cash_flow=cash_flow,
            income_stmt=income_stmt,
        )
        source = YahooFinanceSource(ticker_factory=lambda _: stock, now_factory=lambda: datetime(2026, 4, 11, 3, 0, 0))

        row = source.fetch_stock_data('TEST.BK')

        self.assertEqual(row['Ticker'], 'TEST.BK')
        self.assertEqual(row['Company_Name'], 'Example Public Co')
        self.assertAlmostEqual(row['Revenue'], 1000.0)
        self.assertAlmostEqual(row['FCF'], 100.0)
        self.assertGreater(row['WACC'], 0)
        self.assertEqual(row['Fetched_Date'], '2026-04-11 03:00:00')

    def test_fetch_stock_data_returns_none_on_failure(self):
        source = YahooFinanceSource(ticker_factory=lambda _: (_ for _ in ()).throw(RuntimeError('boom')))
        self.assertIsNone(source.fetch_stock_data('FAIL.BK'))

    def test_fetch_ticker_bundle_includes_statement_observations(self):
        statement_dates = pd.to_datetime(['2025-12-31', '2025-09-30'])
        quarterly_income = pd.DataFrame(
            {
                statement_dates[0]: [1000.0, 120.0, 100.0],
                statement_dates[1]: [900.0, 100.0, 95.0],
            },
            index=['Total Revenue', 'EBIT', 'Diluted Average Shares'],
        )
        quarterly_cash = pd.DataFrame(
            {
                statement_dates[0]: [80.0],
                statement_dates[1]: [70.0],
            },
            index=['Free Cash Flow'],
        )
        quarterly_balance = pd.DataFrame(
            {
                statement_dates[0]: [200.0, 50.0, 100.0],
                statement_dates[1]: [180.0, 40.0, 100.0],
            },
            index=['Total Debt', 'Cash And Cash Equivalents', 'Share Issued'],
        )
        stock = SimpleNamespace(
            info={'currentPrice': 10.0, 'marketCap': 1000.0, 'beta': 1.0},
            cash_flow=quarterly_cash,
            income_stmt=quarterly_income,
            quarterly_cash_flow=quarterly_cash,
            quarterly_income_stmt=quarterly_income,
            quarterly_balance_sheet=quarterly_balance,
            balance_sheet=quarterly_balance,
        )
        source = YahooFinanceSource(ticker_factory=lambda _: stock, now_factory=lambda: datetime(2026, 4, 11, 3, 0, 0))

        bundle = source.fetch_ticker_bundle('TEST.BK', reporting_lag_days=45)

        self.assertIsNotNone(bundle['snapshot'])
        observations = bundle['observations']
        self.assertFalse(observations.empty)
        self.assertIn('Statement_Date', observations.columns)
        self.assertIn('Availability_Date', observations.columns)
        self.assertEqual(observations.iloc[0]['Ticker'], 'TEST.BK')
        self.assertTrue((observations['Reporting_Lag_Days'] == 45).all())


if __name__ == '__main__':
    unittest.main()
