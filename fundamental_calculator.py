#!/usr/bin/env python3
"""
Fundamental Calculator ที่ทำงานกับข้อมูลที่มีอยู่
ใช้ annual 4 ปี + quarterly 6 ไตรมาส อย่างมีประสิทธิภาพ
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional
import numpy as np

class FundamentalCalculator:
    """คำนวณ fundamental metrics จากข้อมูลที่มีอยู่"""

    def __init__(self, research_dir: str = "research_data/latest"):
        self.research_dir = Path(research_dir)
        self.observations = pd.read_csv(self.research_dir / "fundamental_observations.csv")
        self.snapshot = pd.read_csv(self.research_dir / "fundamentals_snapshot.csv")

        # แยก annual และ quarterly
        self.annual = self.observations[self.observations['Period_Type'] == 'annual'].copy()
        self.quarterly = self.observations[self.observations['Period_Type'] == 'quarterly'].copy()

        # แปลงวันที่
        for df in [self.annual, self.quarterly]:
            df['Statement_Date'] = pd.to_datetime(df['Statement_Date'])

    def calculate_4year_average_growth(self, ticker: str) -> Dict[str, float]:
        """คำนวณอัตราเติบโตเฉลี่ย 4 ปีจาก annual data"""

        ticker_annual = self.annual[self.annual['Ticker'] == ticker].copy()

        if len(ticker_annual) < 2:
            return {'error': 'Not enough annual data'}

        # เรียงตามวันที่
        ticker_annual = ticker_annual.sort_values('Statement_Date')

        # ใช้ข้อมูล 4 ปีล่าสุด
        recent_4y = ticker_annual.tail(4)

        if len(recent_4y) < 2:
            return {'error': 'Need at least 2 years of data'}

        # คำนวณ CAGR (Compound Annual Growth Rate)
        first_revenue = recent_4y.iloc[0]['Revenue']
        last_revenue = recent_4y.iloc[-1]['Revenue']

        if first_revenue <= 0:
            return {'error': 'Invalid base revenue'}

        years = len(recent_4y) - 1
        cagr = (last_revenue / first_revenue) ** (1/years) - 1

        # คำนวณ average year-over-year growth
        yoy_growth = recent_4y['Revenue'].pct_change().mean()

        return {
            'cagr_4y': cagr,
            'avg_yoy_growth': yoy_growth,
            'first_year_revenue': first_revenue,
            'last_year_revenue': last_revenue,
            'years_of_data': years + 1
        }

    def get_recent_quarterly_trend(self, ticker: str, quarters: int = 6) -> Dict[str, float]:
        """ดู trend ล่าสุดจาก quarterly data"""

        ticker_quarterly = self.quarterly[self.quarterly['Ticker'] == ticker].copy()

        # กรองเฉพาะที่มี revenue > 0
        ticker_quarterly = ticker_quarterly[ticker_quarterly['Revenue'] > 0].copy()

        if len(ticker_quarterly) < 2:
            return {'error': 'Not enough quarterly data with positive revenue'}

        # ใช้ข้อมูลล่าสุด
        recent_q = ticker_quarterly.tail(min(quarters, len(ticker_quarterly)))

        # คำนวณ trend
        if len(recent_q) >= 2:
            first_q_rev = recent_q.iloc[0]['Revenue']
            last_q_rev = recent_q.iloc[-1]['Revenue']

            quarterly_growth_rate = (last_q_rev / first_q_rev) ** (1/len(recent_q)) - 1

            # Annualize quarterly growth
            annualized_quarterly_growth = (1 + quarterly_growth_rate) ** 4 - 1

            return {
                'quarters_analyzed': len(recent_q),
                'first_quarter_revenue': first_q_rev,
                'last_quarter_revenue': last_q_rev,
                'quarterly_growth_rate': quarterly_growth_rate,
                'annualized_quarterly_growth': annualized_quarterly_growth,
                'trend': 'improving' if last_q_rev > first_q_rev else 'declining'
            }

        return {'error': 'Insufficient quarterly data'}

    def calculate_fundamental_health_score(self, ticker: str) -> Dict[str, any]:
        """คำนวณ fundamental health score รวม"""

        # ดึงข้อมูลล่าสุดจาก snapshot
        ticker_snapshot = self.snapshot[self.snapshot['Ticker'] == ticker]

        if ticker_snapshot.empty:
            return {'error': 'Ticker not found'}

        row = ticker_snapshot.iloc[0]

        # Health metrics
        health_indicators = {
            'positive_fcf': row['FCF'] > 0,
            'positive_revenue': row['Revenue'] > 0,
            'profitable': row['Revenue'] > 0 and row['EBIT'] > 0,
            'reasonable_debt': 0 < row['Debt_to_Equity'] < 200,  # D/E < 2
            'positive_roe': row['ROE'] > 0,
            'positive_roa': row['ROA'] > 0,
            'growing_revenue': row['Revenue_Growth'] > 0,
        }

        health_score = sum(health_indicators.values()) / len(health_indicators)

        return {
            'health_score': health_score,
            'health_indicators': health_indicators,
            'overall_health': 'Strong' if health_score >= 0.7 else 'Moderate' if health_score >= 0.5 else 'Weak'
        }

    def generate_fundamental_report(self, ticker: str) -> Dict[str, any]:
        """สร้างรายงาน fundamental แบบรวม"""

        report = {
            'ticker': ticker,
            'data_availability': {
                'annual_years': len(self.annual[self.annual['Ticker'] == ticker]),
                'quarterly_periods': len(self.quarterly[self.quarterly['Ticker'] == ticker]),
                'meets_minimum_requirement': len(self.annual[self.annual['Ticker'] == ticker]) >= 4
            },
            'long_term_growth': self.calculate_4year_average_growth(ticker),
            'recent_trend': self.get_recent_quarterly_trend(ticker),
            'fundamental_health': self.calculate_fundamental_health_score(ticker),
            'ready_for_analysis': self._is_ready_for_analysis(ticker)
        }

        return report

    def _is_ready_for_analysis(self, ticker: str) -> bool:
        """ตรวจสอบว่าหุ้นพร้อมวิเคราะห์หรือไม่"""

        annual_count = len(self.annual[self.annual['Ticker'] == ticker])
        quarterly_count = len(self.quarterly[self.quarterly['Ticker'] == ticker])

        # ขั้นต่ำ: 4 ปี annual + 4 ไตรมาส quarterly
        return annual_count >= 4 and quarterly_count >= 4

    def generate_all_stocks_report(self) -> pd.DataFrame:
        """สร้างรายงานสรุปทุกหุ้น"""

        all_tickers = self.observations['Ticker'].unique()

        reports = []
        for ticker in all_tickers:
            try:
                report = self.generate_fundamental_report(ticker)
                reports.append({
                    'Ticker': ticker,
                    'Annual_Years': report['data_availability']['annual_years'],
                    'Quarterly_Periods': report['data_availability']['quarterly_periods'],
                    'Meets_Minimum': report['data_availability']['meets_minimum_requirement'],
                    'Ready_for_Analysis': report['ready_for_analysis'],
                    '4Y_CAGR': report['long_term_growth'].get('cagr_4y', np.nan),
                    'Recent_Trend': report['recent_trend'].get('trend', 'N/A'),
                    'Health_Score': report['fundamental_health'].get('health_score', np.nan),
                    'Overall_Health': report['fundamental_health'].get('overall_health', 'N/A')
                })
            except Exception as e:
                reports.append({
                    'Ticker': ticker,
                    'Error': str(e)
                })

        return pd.DataFrame(reports)


def main():
    """ทดสอบการใช้งาน"""

    calculator = FundamentalCalculator()

    print("📊 Fundamental Calculator Ready!")
    print(f"📈 หุ้นทั้งหมด: {len(calculator.observations['Ticker'].unique())} ตัว")
    print(f"📅 Annual records: {len(calculator.annual)}")
    print(f"📝 Quarterly records: {len(calculator.quarterly)}")

    # สร้างรายงานทุกหุ้น
    print("\n🔍 กำลังวิเคราะห์ทุกหุ้น...")
    all_report = calculator.generate_all_stocks_report()

    # บันทึก
    output_dir = Path("research_data/latest")
    all_report.to_csv(output_dir / "fundamental_analysis_report.csv", index=False)

    # สรุป
    ready = len(all_report[all_report['Ready_for_Analysis'] == True])
    not_ready = len(all_report[all_report['Ready_for_Analysis'] == False])

    print(f"\n✅ พร้อมวิเคราะห์: {ready} หุ้น")
    print(f"❌ ยังไม่พร้อม: {not_ready} หุ้น")
    print(f"📁 รายงานถูกบันทึก: research_data/latest/fundamental_analysis_report.csv")

    # แสดงตัวอย่าง
    print(f"\n📊 ตัวอย่าง 5 หุ้นแรกที่พร้อมวิเคราะห์:")
    ready_stocks = all_report[all_report['Ready_for_Analysis'] == True].head(5)
    print(ready_stocks[['Ticker', 'Annual_Years', 'Quarterly_Periods', '4Y_CAGR', 'Recent_Trend', 'Overall_Health']].to_string(index=False))


if __name__ == "__main__":
    main()
