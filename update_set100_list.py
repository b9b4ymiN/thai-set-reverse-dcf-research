#!/usr/bin/env python3
"""
อัปเดตและขยายจาก SET50 เป็น SET100
"""

import re

# SET100 Index Constituents (100 หุ้น)
SET100_TICKERS = [
    # SET50 (50 หุ้น)
    'ADVANC.BK', 'AOT.BK', 'AWC.BK', 'BANPU.BK', 'BBL.BK',
    'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK',
    'BTS.BK', 'CBG.BK', 'CCET.BK', 'CENTEL.BK', 'COM7.BK',
    'CPALL.BK', 'CPF.BK', 'CPN.BK', 'DELTA.BK', 'EA.BK',
    'EGCO.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'HMPRO.BK',
    'IVL.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK',
    'KTC.BK', 'LH.BK', 'MINT.BK', 'OR.BK', 'OSP.BK',
    'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'RATCH.BK', 'SAWAD.BK',
    'SCB.BK', 'SCC.BK', 'SCGP.BK', 'TCAP.BK', 'TIDLOR.BK',
    'TISCO.BK', 'TLI.BK', 'TOP.BK', 'TRUE.BK',

    # Additional SET50 stocks (replacing INTUCH.BK)
    'TTB.BK', 'TU.BK', 'VGI.BK', 'WHA.BK',

    # SET100 additional stocks (50 หุ้น - Mid Cap)
    'BCP.BK', 'BCPG.BK', 'BCH.BK', 'BAY.BK', 'BANK.BK',
    'BBL.BK', 'BJCHI.BK', 'BLA.BK', 'BR.BK', 'BRR.BK',
    'CGD.BK', 'CHG.BK', 'CIMBT.BK', 'CIP.BK', 'CRC.BK',
    'CRC.BK', 'DIF.BK', 'DRT.BK', 'EA.BK', 'EPC.BK',
    'ERW.BK', 'FPT.BK', 'GLOW.BK', 'GPI.BK', 'HANA.BK',
    'HMPRO.BK', 'IFEC.BK', 'III.BK', 'IRPC.BK', 'ITD.BK',
    'JAS.BK', 'JMT.BK', 'KBS.BK', 'KSL.BK', 'LH.BK',
    'LHB.BK', 'MAK.BK', 'MK.BK', 'MTC.BK', 'NCH.BK',
    'NOBLE.BK', 'PCH.BK', 'PF.BK', 'PG.BK', 'PLAN.BK',
    'PRIN.BK', 'PSL.BK', 'RATCH.BK', 'RBF.BK', 'RCL.BK',
    'RML.BK', 'RS.BK', 'SIS.BK', 'SITH.BK', 'SOL.BK',
    'SORO.BK', 'SPALI.BK', 'SPRC.BK', 'STAN.BK', 'STPI.BK',
    'TFF.BK', 'THANI.BK', 'THG.BK', 'TID.BK', 'TIP.BK',
    'TMB.BK', 'TPI.BK', 'TR.BK', 'TRUE.BK', 'TVO.BK',
    'UOB.BK', 'VGI.BK', 'WPH.BK', 'XPG.BK', 'YUWTA.BK'
]

def update_set_stock_fetcher(file_path='set_stock_fetcher.py'):
    """อัปเดต SET_TICKERS ใน set_stock_fetcher.py"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # หา SET_TICKERS list
    pattern = r"SET_TICKERS\s*=\s*\[[^\]]+\]"
    new_list_str = "SET_TICKERS = [\n        " + ",\n        ".join([f"'{ticker}'" for ticker in SET100_TICKERS[:50]]) + "\n    ]"

    # แทนที่ list เดิม (ใช้ 50 หุ้นก่อน)
    new_content = re.sub(pattern, new_list_str, content, count=1)

    if new_content == content:
        print("⚠️  ไม่พบ SET_TICKERS list ในไฟล์")
        return False

    # เขียนไฟล์ใหม่
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ อัปเดต {len(SET100_TICKERS[:50])} หุ้นใน SET_TICKERS แล้ว")
    return True

if __name__ == "__main__":
    print("🔍 อัปเดตรายชื่อ SET50/SET100...")
    print(f"📊 รายชื่อ SET50: {len(SET100_TICKERS[:50])} หุ้น")
    print(f"📈 รายชื่อ SET100: {len(SET100_TICKERS)} หุ้น")

    response = input("\nต้องการอัปเดต set_stock_fetcher.py ใช่ SET50 หรือไม่? (y/n): ")

    if response.lower() == 'y':
        if update_set_stock_fetcher():
            print("\n✅ อัปเดตเสร็จสิ้น!")
            print("\n📝 ขั้นตอนต่อไป:")
            print("   1. python set_stock_fetcher.py  # ดึงข้อมูล SET50")
            print("   2. python -m rdcf.data_pipeline --output-dir research_data/set50")
            print("   3. แก้ไข script นี้เพื่อใช้ SET100 100 หุ้น")
            print("   4. python set_stock_fetcher.py  # ดึงข้อมูล SET100")
            print("   5. python -m rdcf.data_pipeline --output-dir research_data/set100")
        else:
            print("\n❌ อัปเดตไม่สำเร็จ")
    else:
        print("\n❌ ยกเลิกการอัปเดต")
