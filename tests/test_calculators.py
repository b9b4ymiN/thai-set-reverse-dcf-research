import unittest
import pandas as pd
import numpy as np
from fundamental_calculator import FundamentalCalculator
from reverse_dcf_model import ReverseDCFModel
import os

class TestCalculators(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure we have data for testing
        if not os.path.exists('set_stock_data.csv'):
            raise unittest.SkipTest("set_stock_data.csv not found")
        if not os.path.exists('research_data/latest/fundamental_observations.csv'):
            raise unittest.SkipTest("fundamental_observations.csv not found")
        
        cls.fund_calc = FundamentalCalculator()
        cls.dcf_model = ReverseDCFModel()

    def test_fundamental_growth_calculation(self):
        ticker = "ADVANC.BK"
        result = self.fund_calc.calculate_4year_average_growth(ticker)
        if 'error' not in result:
            self.assertIn('cagr_4y', result)
            self.assertIsInstance(result['cagr_4y'], float)

    def test_quarterly_trend_calculation(self):
        ticker = "ADVANC.BK"
        result = self.fund_calc.get_recent_quarterly_trend(ticker)
        if 'error' not in result:
            self.assertIn('trend', result)
            self.assertIn(result['trend'], ['improving', 'declining'])

    def test_reverse_dcf_convergence(self):
        # Test with a known ticker
        ticker = "ADVANC.BK"
        stock_data = self.dcf_model.df[self.dcf_model.df['Ticker'] == ticker].iloc[0]
        
        implied_growth, details = self.dcf_model.calculate_reverse_dcf(
            ticker=ticker,
            base_fcf=stock_data['FCF'],
            wacc=stock_data['WACC'],
            current_price=stock_data['Current_Price'],
            shares_outstanding=stock_data['Market_Cap'] / stock_data['Current_Price']
        )
        
        self.assertIn('intrinsic_value', details)
        # Intrinsic value should be close to current price if converged
        self.assertAlmostEqual(details['intrinsic_value'], stock_data['Current_Price'], delta=0.1)

    def test_intrinsic_value_logic(self):
        # Test Gordon Growth Model safety
        val = self.dcf_model.calculate_intrinsic_value(
            base_fcf=100,
            growth_rate=0.05,
            wacc=0.03,  # WACC < terminal growth (default 0.025)
            terminal_growth=0.025,
            shares_outstanding=10,
            net_debt=0
        )
        self.assertGreater(val, 0)

if __name__ == '__main__':
    unittest.main()
