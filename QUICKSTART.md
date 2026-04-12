# 🚀 Quick Start Guide - Thai SET Reverse DCF Analysis

**โครงการนี้ใช้แนวทาง Reverse DCF ตามกรอบของ Aswath Damodaran**

## 📈 สรุปผลตอบแทนจาก Backtest จริง

ผลจาก 100 หุ้น SET, 20 ไตรมาส (Q2/2021 - Q1/2026), Rebalance รายไตรมาส:

| ตัวชี้วัด | 3 เดือน | 12 เดือน |
|---|---|---|
| ผลตอบแทนสะสม (พอร์ต) | **+36.51%** | **+7.17%** |
| ผลตอบแทนสะสม (SET Benchmark) | -5.08% | -27.54% |
| กำไรจาก 500,000 บาท | **+182,570 บาท** (สิ้นสุด 682,570 บาท) | — |
| Hit Rate | **45%** (9/20 ไตรมาส) | — |
| สัญญาณทั้งหมด | 1,026 | — |

> **Damodaran Framework:** Reverse DCF ไม่ได้มุ่งหา "หุ้นที่ถูกที่สุด" แต่มุ่งถามว่า "ราคาหุ้นสะท้อนความคาดหวังอะไร และความคาดหวังนั้นสมเหตุสมผลไหม" — กรอบนี้ทำให้การลงทุนแบบ Value มีวินัยมากขึ้น

## เริ่มต้นใช้งานง่ายๆ ใน 3 ขั้นตอน

### 📦 ขั้นตอนที่ 1: ติดตั้ง

```bash
cd /home/opc/RDCF
pip install -r requirements.txt
```

### 🔄 ขั้นตอนที่ 2: รันโปรแกรม

**วิธีที่ 1: ใช้ Auto Script (แนะนำ)**
```bash
./run_analysis.sh
```

**วิธีที่ 2: รันทีละขั้นตอน**
```bash
# ดึงข้อมูล
python3 set_stock_fetcher.py

# หรือรัน local demo แบบไม่เรียก live datasource
python3 -m src.pipeline.demo --output-dir research_data/demo

# สร้าง research bundle สำหรับ backtest
python3 -m rdcf.data_pipeline --output-dir research_data/source_of_truth_100 --period 10y --sync-root-snapshot

# รัน backtest
python3 -m src.pipeline.backtest --output-dir research_data/source_of_truth_100/backtest --top-n 10 --horizons 3 6 12 --rebalance-frequency Q --start-date 2020-01-01 --wacc-mode fixed

# สร้าง sector + sensitivity appendix
python3 -m src.pipeline.backtest_analysis --output-dir research_data/source_of_truth_100/backtest --wacc-values 0.06 0.08 0.10 --top-n 10 --horizons 3 6 12 --rebalance-frequency Q --start-date 2020-01-01

# สร้าง figure สำหรับ thesis
python3 -m src.pipeline.backtest_visuals --output-dir research_data/source_of_truth_100/backtest/figures

# รวม thesis bundle
python3 -m src.pipeline.thesis_bundle --output-dir research_data/source_of_truth_100/thesis_bundle

# วิเคราะห์ DCF
python3 reverse_dcf_model.py

# สร้างกราฟ (optional)
python3 visualize_results.py
```

### 📊 ขั้นตอนที่ 3: ดูผลลัพธ์

**ไฟล์ที่ได้:**
- `set_stock_data.csv` - ข้อมูลหุ้นดิบ
- `set_stock_data_quality.csv` - คุณภาพข้อมูล/coverage ของ datasource
- `reverse_dcf_input_exclusions.csv` - หุ้นที่ไม่ผ่าน input filter ของ Reverse DCF
- `set_validation_references.csv` - ลิงก์ SET สำหรับตรวจสอบแบบ manual
- `research_data/source_of_truth_100/manifest.json` - สรุป research bundle สำหรับ backtest
- `research_data/source_of_truth_100/fundamental_observations.csv` - historical statement observations + availability dates
- `research_data/source_of_truth_100/fundamental_coverage.csv` - coverage ของข้อมูล fundamentals แต่ละ ticker
- `research_data/source_of_truth_100/price_history.csv` - ประวัติราคา
- `research_data/source_of_truth_100/price_coverage.csv` - coverage ของประวัติราคาแต่ละ ticker
- `research_data/source_of_truth_100/benchmark_history.csv` - ประวัติ benchmark
- `research_data/source_of_truth_100/backtest/summary.csv` - summary ผลตอบแทนเทียบ benchmark
- `research_data/source_of_truth_100/backtest/exclusions.csv` - หุ้นที่ถูกตัดออกในแต่ละ rebalance พร้อมเหตุผล
- `research_data/source_of_truth_100/backtest/audit_sample.csv` - sample audit สำหรับ no-look-ahead check
- `research_data/source_of_truth_100/backtest/no_lookahead_audit.md` - สรุป no-look-ahead audit แบบ markdown
- `research_data/source_of_truth_100/backtest/report.md` - รายงาน markdown สำหรับ thesis/review
- `research_data/source_of_truth_100/backtest/sector_summary.csv` - สรุปผลตาม sector
- `research_data/source_of_truth_100/backtest/wacc_sensitivity.csv` - sensitivity ต่อสมมติฐาน WACC
- `research_data/source_of_truth_100/backtest/appendix.md` - appendix สำหรับ thesis
- `research_data/source_of_truth_100/backtest/figures/*.png` - figure สำหรับ thesis/presentation
- `research_data/source_of_truth_100/thesis_bundle/` - ชุดไฟล์พร้อมส่งต่อ/แนบ thesis
- ภายใน bundle จะรวม executive summary และ presentation script ด้วย
- และรวม defense outline / Q&A sheet สำหรับการนำเสนอด้วย
- `reverse_dcf_results.csv` - ผลวิเคราะห์ **(สำคัญที่สุด)**
- `set_reverse_dcf_analysis.png` - กราฟสรุป

---

## 📖 อ่านผลลัพธ์

### 1. เปิดไฟล์ reverse_dcf_results.csv

ใช้ Excel, Google Sheets หรือ Python:

```python
import pandas as pd
df = pd.read_csv('reverse_dcf_results.csv')
print(df.head())
```

### 2. สนใจ Column สำคัญเหล่านี้:

| Column | ความหมาย | วิธีอ่าน |
|--------|-----------|----------|
| **Premium_Discount** | ส่วนลด/เพิ่มจากราคาที่เหมาะสม | **+10%↑ = ถูกเกินไป (ซื้อ)**<br>**0% = ราคายุติธรรม**<br>**-10%↓ = แพงเกินไป (ขาย)** |
| **Implied_Growth_Rate** | อัตราเติบโตที่ตลาดคาดหวัง | เทียบกับ Actual_Revenue_Growth<br>ถ้า Implied < Actual → **ซื้อ** |
| **Recommendation** | คำแนะนำ | Undervalued = ซื้อ<br>Fair Value = ถือ<br>Overvalued = ขาย |

### 3. ตัวอย่างการตีความ

**Case 1: BBL.BK**
```
Current_Price: 162.50
Implied_Growth_Rate: 3.2%
Actual_Revenue_Growth: 5.1%
Premium_Discount: +12.5%
Recommendation: UNDervalued - Buy
```
**ความหมาย:**
- ตลาดคาดว่า BBL จะโต 3.2% ต่อปี
- แต่จริงๆ โต 5.1% → **ตลาดมองข้าม**
- ราคาควรจะแพงกว่านี้ 12.5% → **ซื้อ**

**Case 2: CPF.BK**
```
Current_Price: 32.75
Implied_Growth_Rate: 8.5%
Actual_Revenue_Growth: 4.2%
Premium_Discount: -15.3%
Recommendation: OVValued - Reduce
```
**ความหมาย:**
- ตลาดคาดว่า CPF จะโต 8.5% ต่อปี
- แต่จริงๆ โต 4.2% → **ตลาดคาดการณ์สูงไป**
- ราคาแพงเกินไป 15.3% → **ขาย/รอ**

---

## 🎯 การใช้งานขั้นสูง

### หาหุ้นที่ถูกเกินไป (Value Investing)
```python
import pandas as pd

df = pd.read_csv('reverse_dcf_results.csv')

# Undervalued + High ROE
opportunities = df[
    (df['Premium_Discount'] > 10) &  # ถูกกว่ามูลค่า > 10%
    (df['ROE'] > 0.15)  # และ ROE > 15%
].sort_values('Premium_Discount', ascending=False)

print(opportunities[['Ticker', 'Company_Name', 'Premium_Discount', 'ROE']])
```

### หาหุ้นที่ตลาดมองข้าม (Low Expectations)
```python
# ตลาดคาดว่าจะโตน้อย แต่จริงๆ โตเร็ว
ignored_stars = df[
    (df['Implied_Growth_Rate'] < df['Actual_Revenue_Growth']) &  # ตลาดคาดต่ำ
    (df['Growth_Differential'] < -5)  # ต่างกัน > 5%
].sort_values('Growth_Differential')

print(ignored_stars[['Ticker', 'Implied_Growth_Rate', 'Actual_Revenue_Growth']])
```

### กรองตาม Sector
```python
# เฉพาะธนาคาร
banks = df[df['Sector'] == 'Financials']
print(banks[['Ticker', 'Premium_Discount', 'Recommendation']])

# เฉพาะ Energy
energy = df[df['Sector'] == 'Energy']
print(energy[['Ticker', 'Premium_Discount', 'Recommendation']])
```

---

## ⚙️ การปรับแต่ง

### เพิ่มหุ้นที่สนใจ

แก้ไขไฟล์ `set_stock_fetcher.py`:

```python
SET_TICKERS = [
    # เพิ่มหุ้นที่คุณสนใจ
    'YOUR_TICKER.BK',
    'ANOTHER_TICKER.BK',
    ...
]
```

### เปลี่ยน assumptions

แก้ไขไฟล์ `reverse_dcf_model.py`:

```python
terminal_growth = 0.025,  # Terminal growth (2.5% = GDP ไทย long-term)
projection_years = 10,    # Projection period (ปี)
```

---

## ❓ ปัญหาที่พบบ่อย

### Q: ข้อมูลไม่ออก
**A:** Check 3 อย่าง:
1. Internet connected ไหม
2. Yahoo Finance มีข้อมูลหุ้นนั้นไหม
3. Ticker ถูกไหม (ต้องมี .BK)

### Q: จะเช็คคุณภาพ datasource ยังไง
**A:** ดู 3 ไฟล์นี้:
- `set_stock_data_quality.csv` → coverage/missingness ราย field
- `reverse_dcf_input_exclusions.csv` → หุ้นที่ไม่ผ่าน filter
- `set_validation_references.csv` → ลิงก์ SET สำหรับ spot check

### Q: บางหุ้น FCF = 0
**A:** ปกติครับ:
- หุ้่นบางตัวไม่มี cash flow data ใน Yahoo Finance
- ใช้ EPS แทนได้

### Q: Implied Growth สูงผิดปกติ (50%+)
**A:** หุ้่น growth / turnaround:
- Model นี้เหมาะกับ **mature stocks**
- Growth stock ใช้ model อื่น

---

## 📞 ต้องการความช่วยเหลือ

1. **ดู README.md** - รายละเอียดเต็มๆ
2. **ดู comments** ในโค้ด - มีคำอธิบายทุกฟังก์ชัน
3. **Test run** - ลองรันดูก่อน

---

**Remember:** นี่เป็นเพียงเครื่องมือช่วยคิด ไม่ใช่คำแนะนำการลงทุน ใช้ร่วมกับวิจารณญาณของคุณเองด้วยนะครับ 🎯
