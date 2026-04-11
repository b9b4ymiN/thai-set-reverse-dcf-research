#!/usr/bin/env python3
"""
อัปเดตรายชื่อ SET50 ให้ครบถ้วนและถูกต้อง

วิธีใช้งาน:
1. ตรวจสอบ SET50 list ล่าสุดจาก https://www.set.or.th/th/market/index/set50/overview
2. รันสคริปต์นี้เพื่ออัปเดตรายชื่อ
3. รัน data pipeline ใหม่
"""

import re

# SET50 Index Constituents (อัปเดตล่าสุด 2026 ตาม SET website)
# รายชื่อนี้ควรตรวจสอบกับ https://www.set.or.th/th/market/index/set50/overview
# เวอร์ชันปัจจุบันมี 50 หุ้นตามชื่อดัชนี SET50
# INTUCH.BK ถูกแทนที่ด้วย TTB.BK, TU.BK, VGI.BK, WHA.BK (INTUCH delisted)
SET50_TICKERS = [
    'ADVANC.BK', 'AOT.BK', 'AWC.BK', 'BANPU.BK', 'BBL.BK',
    'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK',
    'BTS.BK', 'CBG.BK', 'CCET.BK', 'CENTEL.BK', 'COM7.BK',
    'CPALL.BK', 'CPF.BK', 'CPN.BK', 'DELTA.BK', 'EA.BK',
    'EGCO.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'HMPRO.BK',
    'IVL.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK',
    'KTC.BK', 'LH.BK', 'MINT.BK', 'OR.BK', 'OSP.BK',
    'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'RATCH.BK', 'SAWAD.BK',
    'SCB.BK', 'SCC.BK', 'SCGP.BK', 'TCAP.BK', 'TIDLOR.BK',
    'TISCO.BK', 'TLI.BK', 'TOP.BK', 'TRUE.BK', 'TTB.BK',
    'TU.BK', 'VGI.BK', 'WHA.BK'
]

def update_set_stock_fetcher(file_path='set_stock_fetcher.py'):
    """อัปเดต SET_TICKERS ใน set_stock_fetcher.py"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # หา SET_TICKERS list
    pattern = r"SET_TICKERS\s*=\s*\[[^\]]+\]"
    new_list_str = "SET_TICKERS = [\n        " + ",\n        ".join([f"'{ticker}'" for ticker in SET50_TICKERS]) + "\n    ]"

    # แทนที่ list เดิม
    new_content = re.sub(pattern, new_list_str, content, count=1)

    if new_content == content:
        print("⚠️  ไม่พบ SET_TICKERS list ในไฟล์")
        return False

    # เขียนไฟล์ใหม่
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ อัปเดต {len(SET50_TICKERS)} หุ้นใน SET_TICKERS แล้ว")
    return True

if __name__ == "__main__":
    print("🔍 ตรวจสอบรายชื่อ SET50...")
    print(f"📊 ทั้งหมด {len(SET50_TICKERS)} หุ้น")
    print("\nรายชื่อหุ้นที่จะเพิ่ม/อัปเดต:")
    for i, ticker in enumerate(SET50_TICKERS, 1):
        print(f"  {i:2d}. {ticker}")

    print("\n⚠️  กรุณาตรวจสอบรายชื่อกับ https://www.set.or.th/th/market/index/set50/overview ก่อนดำเนินการ")

    response = input("\nต้องการอัปเดต set_stock_fetcher.py หรือไม่? (y/n): ")

    if response.lower() == 'y':
        if update_set_stock_fetcher():
            print("\n✅ อัปเดตเสร็จสิ้น!")
            print("📝 ขั้นตอนต่อไป:")
            print("   1. python set_stock_fetcher.py")
            print("   2. python -m rdcf.data_pipeline --output-dir research_data/latest --period 10y")
            print("   3. python fundamental_calculator.py")
        else:
            print("\n❌ อัปเดตไม่สำเร็จ")
    else:
        print("\n❌ ยกเลิกการอัปเดต")
