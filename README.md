# Thai SET Reverse DCF Analysis

## 📊 เครื่องมือวิเคราะห์หุ้นไทยด้วย Reverse DCF Model

**โครงการนี้ใช้แนวทาง Reverse DCF ตามกรอบของ Aswath Damodaran**

เครื่องมือนี้ใช้ดึงข้อมูลหุ้นในตลาดหลักทรัพย์ไทย (SET) และคำนวณมูลค่าที่เหมาะสมด้วย **Reverse DCF (Discounted Cash Flow)** ตามกรอบแนวคิดของ Prof. Aswath Damodaran — โดยไม่ได้เริ่มจากการคาดเดาอัตราเติบโต แต่เริ่มจากราคาตลาดแล้วถอยหลังหาว่าตลาด "คาดหวัง" การเติบโตกี่เปอร์เซ็นต์ (Implied Growth Rate)

## 📈 สรุปผลตอบแทน (Return Summary)

ผล Backtest จริงจาก 100 หุ้น SET, 20 ไตรมาส (Q2/2021 - Q1/2026), Rebalance รายไตรมาส:

### ระยะถือ 3 เดือน (3M Horizon, Quarterly Rebalance)
| ตัวชี้วัด | ค่า |
|---|---|
| ผลตอบแทนสะสม (พอร์ต) | **+36.51%** |
| ผลตอบแทนสะสม (SET Benchmark) | **-5.08%** |
| กำไรจากการลงทุน 500,000 บาท | **+182,570 บาท** (มูลค่าสุดท้าย 682,570 บาท) |
| ขาดทุนรายไตรมาสสูงสุด | **-14.73%** (2 ม.ค. 2025) |
| กำไรรายไตรมาสสูงสุด | **+20.25%** (30 มิ.ย. 2025) |
| Hit Rate | **45%** (9/20 ไตรมาส ผลตอบแทนเป็นบวก) |
| สัญญาณทั้งหมด | **1,026** |
| หุ้นที่ถูกห้ามซื้อ (Buy-banned) | **15 ตัว** |

### ระยะถือ 12 เดือน (12M Horizon)
| ตัวชี้วัด | ค่า |
|---|---|
| ผลตอบแทนสะสม (พอร์ต) | **+7.17%** |
| ผลตอบแทนสะสม (SET Benchmark) | **-27.54%** |

> **แนวคิด Damodaran:** Reverse DCF ไม่ได้มุ่งหา "หุ้นที่ถูกที่สุด" แต่มุ่งถามว่า "ราคาหุ้นสะท้อนความคาดหวังอะไร และความคาดหวังนั้นสมเหตุสมผลไหม" — ผลลัพธ์ด้านบนแสดงให้เห็นว่าการถามคำถามนี้อย่างมีวินัย ทำให้พอร์ตเทียบกับ SET ได้ดีกว่าอย่างชัดเจน

## 🎯 คุณสมบัติ

### ข้อมูลที่ดึงมาได้:
- ✅ **ราคาหุ้น** (Current Price, Market Cap)
- ✅ **EPS** (Earnings Per Share)
- ✅ **FCF** (Free Cash Flow)
- ✅ **Revenue Growth Rate**
- ✅ **WACC** (Weighted Average Cost of Capital)
- ✅ ข้อมูลทางการเงินอื่นๆ: ROE, ROA, Debt/Equity, P/E, P/B

### การวิเคราะห์ Reverse DCF:
- 🔮 คำนวณ **Implied Growth Rate** - อัตราเติบโตที่ตลาดคาดหวัง
- 📈 เปรียบเทียบกับ **Actual Revenue Growth** - อัตราเติบโตจริง
- 💰 คำนวณ **Intrinsic Value** - มูลค่าที่เหมาะสม
- 🎯 แนะนำ **Buy/Hold/Sell** ตามความ Value

## 🚀 การติดตั้ง

```bash
# 1. Clone หรือ download โค้ด
cd /home/opc/RDCF

# 2. ติดตั้ง dependencies
pip install -r requirements.txt
```

## 📝 วิธีใช้งาน

### Step 1: ดึงข้อมูลหุ้น (Data Fetching)
```bash
python set_stock_fetcher.py
```

**Output:**
- `set_stock_data.csv` - ไฟล์ข้อมูลหุ้นทั้งหมด
- `set_stock_data_quality.csv` - coverage/missingness ของ datasource
- `reverse_dcf_input_exclusions.csv` - หุ้นที่ผ่าน/ไม่ผ่าน input filter ของ Reverse DCF
- `set_validation_references.csv` - ลิงก์ SET สำหรับ manual validation
- ข้อมูล ~100 หุ้นใหญ่ใน SET
- Summary statistics

### Step 2: วิเคราะห์ Reverse DCF
```bash
python reverse_dcf_model.py
```

### Step 2.5: สร้าง research data bundle สำหรับ backtest
```bash
python -m rdcf.data_pipeline --output-dir research_data/source_of_truth_100 --period 10y --sync-root-snapshot
```

### Step 2.6: รัน backtest
```bash
python -m src.pipeline.backtest --output-dir research_data/source_of_truth_100/backtest --top-n 10 --horizons 3 6 12 --rebalance-frequency Q --start-date 2020-01-01 --wacc-mode fixed
```

### Step 2.7: สร้าง sector/sensitivity appendix
```bash
python -m src.pipeline.backtest_analysis --output-dir research_data/source_of_truth_100/backtest --wacc-values 0.06 0.08 0.10 --top-n 10 --horizons 3 6 12 --rebalance-frequency Q --start-date 2020-01-01
```

### Step 2.8: สร้าง thesis figures
```bash
python -m src.pipeline.backtest_visuals --output-dir research_data/source_of_truth_100/backtest/figures
```

### Step 2.9: รวม thesis bundle
```bash
python -m src.pipeline.thesis_bundle --output-dir research_data/source_of_truth_100/thesis_bundle
```

### Quick demo: สร้าง demo dataset + backtest + figures แบบไม่ใช้ network
```bash
python -m src.pipeline.demo --output-dir research_data/demo
```

**Output:**
- `research_data/demo/dataset/` - deterministic local dataset
- `research_data/demo/backtest/` - summary, audit, appendix, figures
- `research_data/demo/bundle/` - compact thesis-style handoff bundle

### Step 2.6: สร้าง reusable acquisition layer พร้อม provenance tracking
```bash
python scripts/fetch_fundamentals.py --output-root data --period 10y
```

**Output:**
- `reverse_dcf_results.csv` - ผลการวิเคราะห์ทั้งหมด
- Summary Report แสดง:
  - Top Undervalued Stocks
  - Top Overvalued Stocks
  - Highest Implied Growth Rates
  - Sector Analysis

## 📊 ไฟล์ Output

### set_stock_data.csv
ข้อมูลหุ้นดิบ:
```csv
Ticker,Company_Name,Current_Price,EPS,PE_Ratio,Revenue,FCF,WACC,...
BBL.BK,Bangkok Bank,162.50,12.30,13.2,150000M,45000M,0.085,...
CPF.BK,Charoen Pokphand,32.75,2.85,11.5,85000M,12000M,0.092,...
```

### reverse_dcf_results.csv
ผล Reverse DCF:
```csv
Ticker,Current_Price,Implied_Growth_Rate,Actual_Revenue_Growth,Premium_Discount,Recommendation,...
BBL.BK,162.50,3.2%,5.1%,+12.5%,UNDervalued - Buy,...
CPF.BK,32.75,8.5%,4.2%,-15.3%,OVValued - Reduce,...
```

### research_data/source_of_truth_100/
bundle สำหรับงาน backtest/research:
- `fundamentals_snapshot.csv`
- `fundamental_observations.csv` - historical statement observations จาก quarterly/annual statements พร้อม `Statement_Date` และ `Availability_Date`
- `fundamental_coverage.csv`
- `price_history.csv`
- `price_coverage.csv`
- `benchmark_history.csv`
- `datasource_quality.csv`
- `reverse_dcf_exclusions.csv`
- `set_validation_references.csv`
- `manifest.json`

### research_data/source_of_truth_100/backtest/
ผล backtest:
- `signals.csv`
- `portfolio_returns.csv`
- `exclusions.csv`
- `summary.csv`
- `audit_sample.csv`
- `no_lookahead_audit.md`
- `report.md`
- `manifest.json`
- `sector_summary.csv`
- `wacc_sensitivity.csv`
- `appendix.md`
- `figures/active_return_by_horizon.png`
- `figures/hit_rate_by_horizon.png`
- `figures/sector_active_return_heatmap.png`
- `figures/wacc_sensitivity.png`
- `../thesis_bundle/README.md`
- `../thesis_bundle/manifest.json`
- `../thesis_bundle/executive-summary.md`
- `../thesis_bundle/presentation-script.md`
- `../thesis_bundle/defense-outline.md`
- `../thesis_bundle/q-and-a-sheet.md`

### data/
acquisition layout สำหรับ multi-project reuse:
- `raw/set100/{ticker}/fundamentals.json`
- `raw/set100/{ticker}/prices.csv`
- `raw/benchmarks/SET.BK.csv`
- `processed/fundamentals/{quarterly,annual}/fundamentals.parquet`
- `processed/prices/{daily,adjusted}/prices.parquet`
- `processed/metadata/data_manifest.json`
- `processed/metadata/acquisition_log.json`

## 🧠 หลักการ Reverse DCF (ตามกรอบของ Aswath Damodaran)

### แนวคิด
ตามแนวทางของ Prof. Damodaran — แทนที่จะป้อน growth rate เพื่อหา intrinsic value → เรา **ใช้ราคาตลาด** ถอยหลังหา **ว่าตลาดตั้งใจการเติบโตกี่ %** จากนั้นจึงเปรียบเทียบกับผลประกอบการจริง เพื่อดูว่าความคาดหวังของตลาดสมเหตุสมผลหรือไม่

### สูตร DCF มาตรฐาน:
```
Intrinsic Value = PV(FCF₁ to FCF₁₀) + PV(Terminal Value)

Terminal Value = FCF₁₀ × (1 + g) / (WACC - g)
```

### Reverse DCF Process (ตาม Damodaran):
1. เริ่มต้นด้วยราคาตลาดปัจจุบัน
2. ใช้ iterative method หา growth rate ที่ทำให้:
   ```
   DCF Value = Current Market Price
   ```
3. เปรียบเทียบ Implied Growth vs Actual Growth:
   - ถ้า Implied < Actual → **Undervalued** (ตลาดคาดการณ์ต่ำไป)
   - ถ้า Implied > Actual → **Overvalued** (ตลาดคาดการณ์สูงไป)

### การปรับใช้กับตลาดไทย
- ใช้ Country Risk Premium ของไทย (CDS-based 5.87% หรือ Rating-based 7.10%) จากข้อมูลของ Damodaran
- ใช้ Bottom-up Beta ตามอุตสาหกรรม แทน Beta จากการถดถอยโดยตรง
- ใช้ WACC คงที่ในการ Backtest เพื่อป้องกัน Lookahead Bias
- อ้างอิง Terminal Growth = 2.5% (GDP ไทย long-term)

## 📈 การตีความผล

### Premium/Discount:
- **> +10%**: Undervalued - Strong Buy
- **+5% to +10%**: Undervalued - Buy
- **-5% to +5%**: Fair Value - Hold
- **-10% to -5%**: Overvalued - Reduce
- **< -10%**: Overvalued - Avoid

### Growth Differential:
```
Growth Differential = Implied Growth - Actual Growth
```
- **Negative (-)**: ตลาดคาดการณ์ต่ำกว่าจริง → **Opportunity** 🎯
- **Positive (+)**: ตลาดคาดการณ์สูงกว่าจริง → **Caution** ⚠️

## 🎯 ตัวอย่างการใช้งาน

### ต้องการดูหุ้นที่ Undervalued:
```python
import pandas as pd

df = pd.read_csv('reverse_dcf_results.csv')
opportunities = df[df['Premium_Discount'] > 10].sort_values('Premium_Discount', ascending=False)
print(opportunities[['Ticker', 'Company_Name', 'Current_Price', 'Premium_Discount']])
```

### ต้องการกรองตาม Sector:
```python
banks = df[df['Sector'] == 'Financials']
print(banks[['Ticker', 'Implied_Growth_Rate', 'Actual_Revenue_Growth']])
```

## 🔧 การปรับแต่ง

### เพิ่ม Ticker ใหม่:
แก้ไขใน `set_stock_fetcher.py`:
```python
SET_TICKERS = [
    'YOUR_TICKER.BK',  # เพิ่มตรงนี้
    ...
]
```

### ปรับ WACC Calculation:
แก้ไข parameters ใน `set_stock_fetcher.py`:
```python
risk_free_rate = 0.035  # อัตราผลตอบแทนพันธบัตรรัฐบาล
market_risk_premium = 0.06  ความเสี่ยงตลาด
tax_rate = 0.20  # อัตราภาษีเงินได้นิติบุคคล
```

## 📚 อ้างอิง

- **Data Source**: Yahoo Finance (via yfinance API)
- **Primary datasource strategy**: ใช้ Yahoo/yfinance เป็นแหล่งข้อมูลหลัก และใช้หน้าเว็บ SET สำหรับ optional validation
- **Cost**: 100% Free
- **Update Frequency**: Real-time (รันใหม่ได้ตลอด)
- **Research bundle command**: `python -m rdcf.data_pipeline --output-dir research_data/source_of_truth_100 --period 10y`
- **Historical observation rule**: ใช้ statement dates จาก Yahoo statements และตั้ง `Availability_Date` ตาม reporting lag ที่กำหนด

## ⚠️ ข้อจำกัด

1. **Data Quality**: ข้อมูลบางตัวอาจ missing ถ้าไม่มีใน Yahoo Finance
2. **Source Caveat**: Yahoo/yfinance เป็น practical free source ไม่ใช่ official premium market feed
3. **Validation**: ถ้าต้อง spot-check รายตัว ใช้ `set_validation_references.csv` อ้างอิงหน้า SET ได้
4. **Assumptions**:
   - Terminal growth = 2.5% (GDP ไทย long-term)
   - Market risk premium = 6% (Emerging market)
   - Tax rate = 20%
5. **Model Limitations**:
   - ไม่เหมาะกับหุ้่น growth (implied growth จะสูงผิดปกติ)
   - ไม่เหมาะกับหุ้นที่ FCF ติดลบหรือใกล้ 0

## 📞 Support

หากพบปัญหา:
1. Check internet connection
2. Verify ticker symbols (ต้องมี .BK)
3. Check ว่า Yahoo Finance มีข้อมูลหรือไม่

---

**Disclaimer**: เครื่องมือนี้เป็นเพียงการศึกษาและวิเคราะห์ ไม่ใช่คำแนะนำการลงทุน โปรดใช้วิจารณญาณในการตัดสินใจ
