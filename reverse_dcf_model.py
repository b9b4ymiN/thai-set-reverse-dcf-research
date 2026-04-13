#!/usr/bin/env python3
"""
Reverse DCF Model for Thai SET Stocks
Calculates implied growth rates based on current stock prices

Damodaran Framework Alignment
==============================
This module implements the reverse DCF methodology following Aswath Damodaran's
valuation framework:

- 2-stage DCF with linear growth decay (Damodaran, *Investment Valuation*, Ch.12)
- Terminal value via the Gordon Growth Model (Damodaran, *Investment Valuation*, Ch.12)
- Growth differential as implied-vs-actual growth gap (Damodaran, *Investment Valuation*, Ch.25)

Key Damodaran references:
  - Damodaran, A. (2012). *Investment Valuation*, 3rd ed., Wiley. Chapters 12-14, 25.
  - Damodaran, A. (2006). *Damodaran on Valuation*, 2nd ed., Wiley. Chapter 5.
  - NYU Stern lecture notes: pages.stern.nyu.edu/~adamodar/
  - Blog & quarterly data updates: aswathdamodaran.blogspot.com
  - Thai SET adaptation guide: docs/damodaran-stern-datasets-thai-set.md

Formula-to-Damodaran mapping: .omc/drafts/formula-damodaran-mapping.md
"""

import pandas as pd
import numpy as np
from typing import Tuple
import warnings
warnings.filterwarnings('ignore')


def calculate_intrinsic_value_static(base_fcf: float,
                                     growth_rate: float,
                                     wacc: float,
                                     terminal_growth: float,
                                     shares_outstanding: float,
                                     net_debt: float = 0,
                                     projection_years: int = 10) -> float:
    """Calculate intrinsic value per share using a 2-stage DCF model.

    Damodaran 2-stage DCF structure (*Investment Valuation*, Ch.12; *Damodaran on
    Valuation*, Ch.5):

    - Stage 1 (years 1-5): FCF grows at the constant high-growth rate.
    - Stage 2 (years 6-10): Growth linearly decays from the high-growth rate to
      the terminal growth rate, with each year's FCF chained from the prior year.
    - Terminal value uses the Gordon Growth Model:
      TV = FCF_N * (1 + g_terminal) / (WACC - g_terminal).

    The terminal growth guard ensures g_terminal < WACC (Damodaran's requirement
    that the perpetual growth rate cannot exceed the discount rate).

    Args:
        base_fcf: Free cash flow in the base year.
        growth_rate: High-growth rate for stage 1 (decimal, e.g. 0.10 for 10%).
        wacc: Weighted average cost of capital (decimal).
        terminal_growth: Long-run stable growth rate (decimal, e.g. 0.025).
        shares_outstanding: Total shares outstanding.
        net_debt: Total debt minus cash (default 0).
        projection_years: Total projection horizon (default 10).

    Returns:
        Intrinsic value per share.
    """

    fcf_forecast = []
    discount_factors = []
    prev_fcf = base_fcf

    for year in range(1, projection_years + 1):
        if year <= 5:
            # Stage 1: constant high-growth (Damodaran, Investment Valuation Ch.12)
            fcf = prev_fcf * (1 + growth_rate)
        else:
            # Stage 2: linear growth decay toward terminal rate
            # (Damodaran, Investment Valuation Ch.12 — 2-stage DCF with transition)
            remaining_years = year - 5
            declining_growth = growth_rate - ((growth_rate - terminal_growth) * (remaining_years / 5))
            fcf = prev_fcf * (1 + declining_growth)

        fcf_forecast.append(fcf)
        discount_factors.append(1 / (1 + wacc) ** year)
        prev_fcf = fcf

    pv_fcf = sum(fcf * df for fcf, df in zip(fcf_forecast, discount_factors))

    # Terminal growth guard: g_terminal must be < WACC
    # (Damodaran, Investment Valuation Ch.12 — perpetual growth constraint)
    if wacc <= terminal_growth:
        terminal_growth = wacc - 0.005

    # Terminal value via Gordon Growth Model (Damodaran, Investment Valuation Ch.12)
    terminal_fcf = fcf_forecast[-1] * (1 + terminal_growth)
    terminal_value = terminal_fcf / (wacc - terminal_growth)
    pv_terminal_value = terminal_value * discount_factors[-1]
    enterprise_value = pv_fcf + pv_terminal_value
    equity_value = enterprise_value - net_debt
    return equity_value / shares_outstanding


def solve_reverse_dcf(base_fcf: float,
                      wacc: float,
                      current_price: float,
                      shares_outstanding: float,
                      net_debt: float = 0,
                      initial_growth_guess: float = 0.05,
                      tolerance: float = 0.001,
                      max_iterations: int = 1000) -> Tuple[float, dict]:
    """Solve for the implied growth rate given market price and DCF assumptions.

    This is the core of the reverse DCF approach: rather than projecting growth
    and deriving value, we observe the market price and back-solve the growth
    rate that would justify it. This follows Damodaran's "what is the market
    pricing in?" framing (*Investment Valuation*, Ch.25; NYU Stern DCF lectures).

    Uses binary search over growth rates [-50%, +100%] — the wide bounds are an
    implementation choice, not a Damodaran prescription, but cover the plausible
    range for both distressed and hyper-growth scenarios.

    The safe terminal growth is capped at 2.5% (consistent with Damodaran's
    guidance that terminal growth should not exceed long-term risk-free rate or
    nominal GDP growth) with a floor ensuring g_terminal < WACC.
    """
    if base_fcf <= 0 or current_price <= 0 or shares_outstanding <= 0:
        return 0.0, {'error': 'Invalid inputs'}

    # Binary search bounds: [-50%, +100%] — implementation choice covering
    # distressed to hyper-growth scenarios (no specific Damodaran prescription)
    low = -0.50
    high = 1.00

    for iteration in range(max_iterations):
        mid = (low + high) / 2
        # Terminal growth cap: Damodaran rule g_terminal <= Rf (Investment Valuation Ch.12)
        # For Thai equities, Rf ~3.5% in recent years, so cap at 3.5% (not hardcoded 2.5%)
        # Floor at 0.5% and must be at least 1% below WACC for convergence
        rf_cap = 0.035  # Thai 10Y bond yield approximation for current era
        safe_terminal_growth = min(rf_cap, max(wacc - 0.01, 0.005))
        intrinsic_value = calculate_intrinsic_value_static(
            base_fcf=base_fcf,
            growth_rate=mid,
            wacc=wacc,
            terminal_growth=safe_terminal_growth,
            shares_outstanding=shares_outstanding,
            net_debt=net_debt
        )
        diff = intrinsic_value - current_price

        if abs(diff) < tolerance:
            return mid, {
                'implied_growth': mid,
                'intrinsic_value': intrinsic_value,
                'current_price': current_price,
                'premium_discount': (intrinsic_value / current_price) - 1,
                'iterations': iteration + 1,
                'converged': True,
            }

        if intrinsic_value > current_price:
            high = mid
        else:
            low = mid

    return mid, {
        'implied_growth': mid,
        'intrinsic_value': intrinsic_value,
        'current_price': current_price,
        'premium_discount': (intrinsic_value / current_price) - 1,
        'iterations': max_iterations,
        'converged': False
    }


class ReverseDCFModel:
    """
    Reverse DCF Calculator
    Back-solves the growth rate implied by current stock price
    """

    def __init__(self, data_file: str = 'set_stock_data.csv'):
        """Initialize with stock data"""
        self.df = pd.read_csv(data_file)
        print(f"Loaded {len(self.df)} stocks from {data_file}")

    def calculate_reverse_dcf(self,
                             ticker: str,
                             base_fcf: float,
                             wacc: float,
                             current_price: float,
                             shares_outstanding: float,
                             initial_growth_guess: float = 0.05,
                             tolerance: float = 0.001,
                             max_iterations: int = 1000) -> Tuple[float, dict]:
        """
        Calculate the growth rate implied by current stock price using iterative approach
        """

        if base_fcf <= 0 or current_price <= 0 or shares_outstanding <= 0:
            return 0.0, {'error': 'Invalid inputs'}

        # Get net debt from self.df
        stock_data = self.df[self.df['Ticker'] == ticker]
        net_debt = 0
        if not stock_data.empty:
            total_debt = stock_data.iloc[0].get('Total_Debt', 0)
            total_cash = stock_data.iloc[0].get('Total_Cash', 0)
            net_debt = total_debt - total_cash

        return solve_reverse_dcf(
            base_fcf=base_fcf,
            wacc=wacc,
            current_price=current_price,
            shares_outstanding=shares_outstanding,
            net_debt=net_debt,
            initial_growth_guess=initial_growth_guess,
            tolerance=tolerance,
            max_iterations=max_iterations
        )

    def calculate_intrinsic_value(self,
                                 base_fcf: float,
                                 growth_rate: float,
                                 wacc: float,
                                 terminal_growth: float,
                                 shares_outstanding: float,
                                 net_debt: float = 0,
                                 projection_years: int = 10) -> float:
        """
        Calculate intrinsic value using DCF
        """

        return calculate_intrinsic_value_static(
            base_fcf=base_fcf,
            growth_rate=growth_rate,
            wacc=wacc,
            terminal_growth=terminal_growth,
            shares_outstanding=shares_outstanding,
            net_debt=net_debt,
            projection_years=projection_years
        )

    def run_reverse_dcf_analysis(self) -> pd.DataFrame:
        """Run Reverse DCF analysis on all stocks"""

        results = []

        for idx, row in self.df.iterrows():
            ticker = row['Ticker']
            current_price = row['Current_Price']
            fcf = row['FCF']
            wacc = row['WACC']
            market_cap = row['Market_Cap']

            # Calculate shares outstanding
            if current_price > 0:
                shares_outstanding = market_cap / current_price
            else:
                shares_outstanding = 0

            if fcf > 0 and wacc > 0 and current_price > 0 and shares_outstanding > 0:
                implied_growth, details = self.calculate_reverse_dcf(
                    ticker=ticker,
                    base_fcf=fcf,
                    wacc=wacc,
                    current_price=current_price,
                    shares_outstanding=shares_outstanding
                )

                result = {
                    'Ticker': ticker,
                    'Company_Name': row['Company_Name'],
                    'Sector': row['Sector'],
                    'Current_Price': current_price,
                    'Market_Cap_B': market_cap / 1e9,
                    'FCF_M': fcf / 1e6,
                    'WACC': wacc,
                    'EPS': row['EPS'],
                    'PE_Ratio': row['PE_Ratio'],
                    'Actual_Revenue_Growth': row['Revenue_Growth'],
                    'Implied_Growth_Rate': implied_growth * 100,  # Convert to percentage
                    'Intrinsic_Value': details.get('intrinsic_value', 0),
                    'Premium_Discount': details.get('premium_discount', 0) * 100,  # Percentage
                    # Growth differential: implied - actual (Damodaran reverse DCF framing, Ch.25)
                    # Negative = market expects less than history = potential undervaluation
                    'Growth_Differential': (implied_growth - row['Revenue_Growth']) * 100,
                    'ROE': row['ROE'],
                    'Debt_to_Equity': row['Debt_to_Equity'],
                    'Recommendation': self._get_recommendation(implied_growth, row['Revenue_Growth'], details)
                }

                results.append(result)

        results_df = pd.DataFrame(results)
        return results_df

    def _get_recommendation(self, implied_growth: float, actual_growth: float, details: dict) -> str:
        """Generate investment recommendation based on Reverse DCF.

        The growth differential (implied - actual) follows Damodaran's reverse
        DCF interpretation: when the market implies lower growth than fundamentals
        show, the stock may be undervalued (*Investment Valuation*, Ch.25).
        """

        # Growth differential: Implied Growth - Actual Growth
        # Negative means market expects less than historical -> potential opportunity
        diff = (implied_growth - actual_growth) * 100

        # Also consider if it converged
        if not details.get('converged', True):
            return 'UNRELIABLE - No Convergence'

        if diff < -10:  # Market expects >10% LESS than history
            return 'UNDervalued - Strong Buy'
        elif diff < -5:
            return 'UNDervalued - Buy'
        elif diff < 5:  # Within 5% of history
            return 'Fair Value - Hold'
        elif diff < 10:
            return 'OVValued - Reduce'
        else:
            return 'OVValued - Avoid'

    def generate_summary_report(self, results_df: pd.DataFrame):
        """Generate comprehensive summary report"""

        # Filter out unreliable results for summary statistics
        reliable_df = results_df[results_df['Recommendation'] != 'UNRELIABLE - No Convergence']

        print("\n" + "=" * 80)
        print("REVERSE DCF ANALYSIS SUMMARY")
        print("=" * 80)

        # Overall statistics
        print("\n📊 MARKET-WIDE STATISTICS")
        print("-" * 80)
        print(f"Total Stocks Analyzed: {len(results_df)}")
        print(f"Reliable Analyses: {len(reliable_df)}")
        print(f"Average Implied Growth Rate: {reliable_df['Implied_Growth_Rate'].mean():.2f}%")
        print(f"Median Implied Growth Rate: {reliable_df['Implied_Growth_Rate'].median():.2f}%")
        print(f"Average WACC: {reliable_df['WACC'].mean() * 100:.2f}%")

        # Growth differential analysis
        print("\n📈 GROWTH ANALYSIS")
        print("-" * 80)
        print(f"Average Actual Revenue Growth: {reliable_df['Actual_Revenue_Growth'].mean() * 100:.2f}%")
        print(f"Average Implied Growth: {reliable_df['Implied_Growth_Rate'].mean():.2f}%")
        print(f"Average Growth Differential: {reliable_df['Growth_Differential'].mean():.2f}%")

        # Valuation distribution based on recommendation
        print("\n💰 VALUATION DISTRIBUTION")
        print("-" * 80)
        undervalued = len(results_df[results_df['Recommendation'].str.contains('UNDervalued')])
        fair_value = len(results_df[results_df['Recommendation'].str.contains('Fair Value')])
        overvalued = len(results_df[results_df['Recommendation'].str.contains('OVValued')])
        unreliable = len(results_df[results_df['Recommendation'].str.contains('UNRELIABLE')])

        print(f"Undervalued: {undervalued} stocks ({undervalued/len(results_df)*100:.1f}%)")
        print(f"Fair Value: {fair_value} stocks ({fair_value/len(results_df)*100:.1f}%)")
        print(f"Overvalued: {overvalued} stocks ({overvalued/len(results_df)*100:.1f}%)")
        print(f"Unreliable: {unreliable} stocks ({unreliable/len(results_df)*100:.1f}%)")

        # Top opportunities (Lowest Growth Differential)
        print("\n🎯 TOP 10 MOST UNDERVALUED STOCKS (Highest Margin of Safety)")
        print("-" * 80)
        top_undervalued = reliable_df.nsmallest(10, 'Growth_Differential')[['Ticker', 'Company_Name', 'Implied_Growth_Rate', 'Actual_Revenue_Growth', 'Growth_Differential', 'Current_Price']]
        print(top_undervalued.to_string(index=False))

        # Most overvalued (Highest Growth Differential)
        print("\n⚠️  TOP 10 MOST OVERVALUED STOCKS (Market Expects High Growth)")
        print("-" * 80)
        top_overvalued = reliable_df.nlargest(10, 'Growth_Differential')[['Ticker', 'Company_Name', 'Implied_Growth_Rate', 'Actual_Revenue_Growth', 'Growth_Differential', 'Current_Price']]
        print(top_overvalued.to_string(index=False))

        # Sector analysis
        if 'Sector' in results_df.columns:
            print("\n🏭 SECTOR ANALYSIS (Average Growth Differential)")
            print("-" * 80)
            sector_analysis = reliable_df.groupby('Sector').agg({
                'Growth_Differential': 'mean',
                'Implied_Growth_Rate': 'mean',
                'Ticker': 'count'
            }).round(2)
            sector_analysis.columns = ['Avg_Growth_Diff%', 'Avg_Implied_Growth%', 'Count']
            print(sector_analysis.sort_values('Avg_Growth_Diff%').to_string())

    def save_results(self, results_df: pd.DataFrame, filename: str = 'reverse_dcf_results.csv'):
        """Save Reverse DCF results to CSV"""
        results_df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n✓ Results saved to {filename}")

    def export_detailed_model(self, results_df: pd.DataFrame, ticker: str):
        """Export detailed DCF model for specific stock"""

        stock_data = results_df[results_df['Ticker'] == ticker]

        if stock_data.empty:
            print(f"No data found for {ticker}")
            return

        # Get original data
        original_data = self.df[self.df['Ticker'] == ticker].iloc[0]

        print(f"\n{'=' * 80}")
        print(f"DETAILED REVERSE DCF MODEL: {ticker} - {original_data['Company_Name']}")
        print(f"{'=' * 80}")

        print(f"\n📊 COMPANY METRICS")
        print("-" * 80)
        print(f"Current Price: ฿{original_data['Current_Price']:.2f}")
        print(f"Market Cap: ฿{original_data['Market_Cap']/1e9:.2f}B")
        print(f"EPS: ฿{original_data['EPS']:.2f}")
        print(f"P/E Ratio: {original_data['PE_Ratio']:.2f}x")
        print(f"ROE: {original_data['ROE']*100:.2f}%")
        print(f"Revenue Growth: {original_data['Revenue_Growth']*100:.2f}%")

        print(f"\n💰 CASH FLOW DATA")
        print("-" * 80)
        print(f"Free Cash Flow: ฿{original_data['FCF']/1e6:.2f}M")

        print(f"\n🎯 DISCOUNT FACTORS")
        print("-" * 80)
        print(f"WACC: {original_data['WACC']*100:.2f}%")
        print(f"Beta: {original_data['Beta']:.2f}")
        print(f"Cost of Equity: {original_data['Cost_of_Equity']*100:.2f}%")
        print(f"Cost of Debt: {original_data['Cost_of_Debt']*100:.2f}%")

        row = stock_data.iloc[0]
        print(f"\n🔮 REVERSE DCF RESULTS")
        print("-" * 80)
        print(f"Implied Growth Rate: {row['Implied_Growth_Rate']:.2f}%")
        print(f"Actual Revenue Growth: {row['Actual_Revenue_Growth']*100:.2f}%")
        print(f"Growth Differential: {row['Growth_Differential']:.2f}%")
        print(f"Intrinsic Value: ฿{row['Intrinsic_Value']:.2f}")
        print(f"Premium/Discount: {row['Premium_Discount']:.2f}%")
        print(f"Recommendation: {row['Recommendation']}")


def main():
    """Main execution function"""

    # Load data and run Reverse DCF
    model = ReverseDCFModel('set_stock_data.csv')
    results = model.run_reverse_dcf_analysis()

    # Generate summary report
    model.generate_summary_report(results)

    # Save results
    model.save_results(results, 'reverse_dcf_results.csv')

    # Export detailed model for a sample stock
    if len(results) > 0:
        sample_ticker = results.iloc[0]['Ticker']
        model.export_detailed_model(results, sample_ticker)

    print("\n" + "=" * 80)
    print("✓ Reverse DCF Analysis Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
