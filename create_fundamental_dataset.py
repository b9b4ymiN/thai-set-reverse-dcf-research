#!/usr/bin/env python3
"""
สร้าง Fundamental Dataset ที่ครบถ้วนสำหรับการวิเคราะห์
รวมข้อมูล annual + quarterly ให้พร้อมใช้งาน
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

def create_complete_fundamental_dataset():
    """สร้าง dataset ที่รวมทุกอย่างไว้ในที่เดียว"""

    # อ่านข้อมูลจาก research_data/latest
    research_dir = Path("research_data/latest")

    # 1. อ่าน fundamental observations (มีทั้ง annual และ quarterly)
    observations = pd.read_csv(research_dir / "fundamental_observations.csv")

    # 2. อ่าน snapshot ล่าสุด
    snapshot = pd.read_csv(research_dir / "fundamentals_snapshot.csv")

    # 3. กรองเฉพาะข้อมูลที่มีคุณภาพ (4 ปีย้อนหลัง)
    four_years_ago = datetime.now() - timedelta(days=4*365)
    observations['Statement_Date'] = pd.to_datetime(observations['Statement_Date'])

    recent_observations = observations[
        observations['Statement_Date'] >= four_years_ago
    ].copy()

    # 4. สร้าง dataset ที่แยกประเภท
    annual_data = recent_observations[recent_observations['Period_Type'] == 'annual']
    quarterly_data = recent_observations[recent_observations['Period_Type'] == 'quarterly']

    # 5. สรุปสถิติ
    stats = {
        'total_stocks': observations['Ticker'].nunique(),
        'stocks_with_4years': len([t for t in observations['Ticker'].unique()
                                 if len(observations[observations['Ticker'] == t]) >= 16]),  # 4 annual + 12 quarterly
        'annual_records': len(annual_data),
        'quarterly_records': len(quarterly_data),
        'date_range': f"{observations['Statement_Date'].min()} to {observations['Statement_Date'].max()}"
    }

    # 6. บันทึก output
    output_dir = Path("research_data/latest")

    # Dataset รวม
    recent_observations.to_csv(output_dir / "fundamental_complete.csv", index=False)

    # Annual only
    annual_data.to_csv(output_dir / "fundamental_annual_only.csv", index=False)

    # Quarterly only
    quarterly_data.to_csv(output_dir / "fundamental_quarterly_only.csv", index=False)

    # Statistics
    with open(output_dir / "fundamental_stats.json", 'w') as f:
        import json
        json.dump(stats, f, indent=2, default=str)

    print("✅ Fundamental Dataset สร้างเสร็จแล้ว!")
    print(f"📊 หุ้นทั้งหมด: {stats['total_stocks']} ตัว")
    print(f"📈 หุ้นที่มีข้อมูลครบ 4 ปี: {stats['stocks_with_4years']} ตัว")
    print(f"📅 ช่วงเวลา: {stats['date_range']}")
    print(f"📝 Annual records: {stats['annual_records']}")
    print(f"📝 Quarterly records: {stats['quarterly_records']}")

    return stats

if __name__ == "__main__":
    create_complete_fundamental_dataset()
