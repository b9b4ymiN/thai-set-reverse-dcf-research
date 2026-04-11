#!/usr/bin/env python3
"""
วิเคราะห์ช่องว่างของข้อมูล fundamental
เพื่อวางแผนเติมข้อมูลให้ครบตามเป้าหมาย
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

def analyze_fundamental_gaps():
    """วิเคราะห์หุ้นแต่ละตัวว่ามีข้อมูลครบหรือยัง"""

    research_dir = Path("research_data/latest")
    observations = pd.read_csv(research_dir / "fundamental_observations.csv")
    observations['Statement_Date'] = pd.to_datetime(observations['Statement_Date'])

    # วิเคราะห์ทีละหุ้น
    analysis = []

    for ticker in observations['Ticker'].unique():
        ticker_data = observations[observations['Ticker'] == ticker]

        annual = ticker_data[ticker_data['Period_Type'] == 'annual']
        quarterly = ticker_data[ticker_data['Period_Type'] == 'quarterly']

        # นับข้อมูลในช่วง 4 ปีล่าสุด
        four_years_ago = datetime.now() - timedelta(days=4*365)
        recent_annual = annual[annual['Statement_Date'] >= four_years_ago]
        recent_quarterly = quarterly[quarterly['Statement_Date'] >= four_years_ago]

        # คำนวณความครบถ้วน
        expected_annual = 4  # 4 ปี
        expected_quarterly = 16  # 4 ปี * 4 ไตรมาส

        annual_gap = expected_annual - len(recent_annual)
        quarterly_gap = expected_quarterly - len(recent_quarterly)

        # หาช่วงเวลาที่ขาด
        missing_periods = []
        if annual_gap > 0:
            missing_periods.append(f"{annual_gap} annual records")
        if quarterly_gap > 0:
            missing_periods.append(f"{quarterly_gap} quarterly records")

        analysis.append({
            'Ticker': ticker,
            'Annual_Count': len(recent_annual),
            'Quarterly_Count': len(recent_quarterly),
            'Total_Records': len(ticker_data),
            'Date_Range': f"{ticker_data['Statement_Date'].min().date()} to {ticker_data['Statement_Date'].max().date()}",
            'Missing_Data': ', '.join(missing_periods) if missing_periods else 'COMPLETE',
            'Status': '✅ COMPLETE' if (annual_gap == 0 and quarterly_gap == 0) else '❌ INCOMPLETE'
        })

    # สร้าง DataFrame
    df_analysis = pd.DataFrame(analysis)
    df_analysis = df_analysis.sort_values('Status')

    # บันทึกผล
    output_dir = Path("research_data/latest")
    df_analysis.to_csv(output_dir / "fundamental_gap_analysis.csv", index=False)

    # สรุป
    complete = len(df_analysis[df_analysis['Status'] == '✅ COMPLETE'])
    incomplete = len(df_analysis[df_analysis['Status'] == '❌ INCOMPLETE'])

    print(f"📊 วิเคราะห์ข้อมูล fundamental ทั้งหมด {len(df_analysis)} หุ้น")
    print(f"✅ ครบตามเป้าหมาย (4 ปี + quarterly): {complete} หุ้น")
    print(f"❌ ยังไม่ครบ: {incomplete} หุ้น")
    print(f"\n📁 รายละเอียดถูกบันทึกไว้ที่: research_data/latest/fundamental_gap_analysis.csv")

    # แสดงตัวอย่าง 10 หุ้นแรกที่ยังไม่ครบ
    if incomplete > 0:
        print(f"\n🔍 ตัวอย่าง 10 หุ้นแรกที่ยังไม่ครบ:")
        incomplete_df = df_analysis[df_analysis['Status'] == '❌ INCOMPLETE'].head(10)
        print(incomplete_df[['Ticker', 'Annual_Count', 'Quarterly_Count', 'Missing_Data']].to_string(index=False))

    return df_analysis

if __name__ == "__main__":
    analyze_fundamental_gaps()
