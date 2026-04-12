# คู่มือการทดสอบย้อนหลัง (Backtesting Guide)

โครงการนี้ใช้แนวทาง Reverse DCF ตามกรอบของ Aswath Damodaran

## สรุปผลตอบแทน (Return Summary)

ผล Backtest จริงจาก 100 หุ้น SET, 20 ไตรมาส (Q2/2021 - Q1/2026), Rebalance รายไตรมาส:

### ระยะถือ 3 เดือน (3M Horizon)
| ตัวชี้วัด | ค่า |
|---|---|
| ผลตอบแทนสะสม (พอร์ต) | **+36.51%** |
| ผลตอบแทนสะสม (ดัชนี SET) | **-5.08%** |
| ลงทุน 500,000 บาท → มูลค่าสุดท้าย | **682,570 บาท** (กำไร 182,570 บาท) |
| กำไรรายไตรมาสสูงสุด | **+20.25%** (30 มิ.ย. 2025) |
| ขาดทุนรายไตรมาสสูงสุด | **-14.73%** (2 ม.ค. 2025) |
| อัตราความสำเร็จ (Hit Rate) | **45%** (9/20 ไตรมาสเป็นบวก) |
| สัญญาณทั้งหมด | **1,026** |
| หุ้นที่ถูกห้ามซื้อ | **15 ตัว** |

### ระยะถือ 12 เดือน (12M Horizon)
| ตัวชี้วัด | ค่า |
|---|---|
| ผลตอบแทนสะสม (พอร์ต) | **+7.17%** |
| ผลตอบแทนสะสม (ดัชนี SET) | **-27.54%** |

> **บริบท:** กรอบ Reverse DCF ของ Damodaran ไม่ได้มุ่งหา "หุ้นที่ถูกที่สุด" แต่มุ่งถามว่า "ราคาหุ้นสะท้อนความคาดหวังอะไร และความคาดหวังนั้นสมเหตุสมผลไหม" — ผลลัพธ์ด้านบนแสดงให้เห็นว่าการถามคำถามนี้อย่างมีวินัย ทำให้พอร์ตเทียบกับ SET ได้ดีกว่าอย่างชัดเจน

## สาธิตการใช้งาน (Quick Demo)

```bash
python3 -m src.pipeline.demo --output-dir research_data/demo
```

คำสั่งนี้สร้างชุดข้อมูลที่กำหนดได้ (deterministic) บวกกับสรุป backtest, appendix, กราฟ, และ thesis-style bundle โดยไม่ต้องดึงข้อมูลจากแหล่งภายนอก

## คำสั่งหลัก

```bash
python -m src.pipeline.backtest \
  --output-dir research_data/source_of_truth_100/backtest \
  --top-n 10 \
  --horizons 3 6 12 \
  --rebalance-frequency Q \
  --start-date 2020-01-01
```

## ข้อมูลนำเข้า

- `research_data/source_of_truth_100/fundamentals_snapshot.csv`
- `research_data/source_of_truth_100/fundamental_observations.csv`
- `research_data/source_of_truth_100/price_history.csv`
- `research_data/source_of_truth_100/benchmark_history.csv`

## วิธีการ (Methodology)

Backtest ใช้แนวทาง Reverse DCF ตามกรอบของ Prof. Aswath Damodaran
สำหรับรายละเอียดการจัดวางวิธีการและการแมปสูตรกับ Damodaran ดู [`METHODOLOGY.md`](../METHODOLOGY.md)

### การปรับพอร์ตรายไตรมาสเมื่อ Fundamentals เปลี่ยน

การปรับพอร์ต (Rebalancing) เกิดขึ้นทุกไตรมาส (`--rebalance-frequency Q`) โดยจังหวะตรงกับรอบการรายงานผลประกอบการของบริษัทจดทะเบียนไทย ไม่ใช่ตารางเวลาตามปฏิทินโดยพลการ — พอร์ตจะหมุนเปลี่ยนเมื่อพื้นฐาน (fundamentals) เปลี่ยนแปลง:

1. ในแต่ละวัน rebalance จะใช้เฉพาะข้อมูลที่มี `Availability_Date <= Rebalance_Date` เท่านั้น ดังนั้นพอร์ตจะตอบสนองต่องบการเงินที่เพิ่งเปิดเผย ไม่ใช่ข้อมูลเก่า
2. ราคาตลาดจะใช้ราคา ณ วัน rebalance (หรือวันซื้อขายสุดท้ายก่อนหน้า)
3. คะแนนสัญญาณ (Signal Scores) ที่อัปเดตแล้วจะจัดอันดับใหม่ ทำให้การถือครองหมุนเปลี่ยนตามธรรมชาติเมื่อพื้นฐานของบริษัทเปลี่ยนแปลงเมื่อเทียบกับความคาดหวังที่ราคาตลาดสะท้อน

### การสร้างสัญญาณ (Signal Construction)

ตามแนวทางของ Damodaran สำหรับแต่ละหุ้นที่มีสิทธิ์ในแต่ละวัน rebalance:

1. เลือกข้อมูลล่าสุดที่ `Availability_Date <= Rebalance_Date`
2. เอาราคาปรับแล้ว (adjusted price) ล่าสุด ณ หรือก่อนวัน rebalance
3. แก้ Reverse DCF โดยใช้:
   - FCF จากข้อมูลที่มีวันที่
   - จำนวนหุ้นจาก diluted/issued shares
   - Net debt จากข้อมูลที่มีวันที่
   - WACC จาก **สมมติฐานคงที่** (`--wacc-mode fixed`, ค่าเริ่มต้น) เพื่อป้องกันการรั่วไหลของข้อมูลอนาคต (Damodaran เตือนไม่ให้ใช้ WACC จากช่วงเวลาปัจจุบันกับการประเมินมูลค่าย้อนหลัง — ดู [`docs/damodaran-stern-datasets-thai-set.md`](damodaran-stern-datasets-thai-set.md))
4. จัดอันดับตาม `Signal_Score = Actual_Revenue_Growth - Implied_Growth_Rate`
   - คะแนนบวก: การเติบโตที่เกิดขึ้นจริงเกินความคาดหวังที่ตลาดสะท้อน (อาจถูกเกินไป)
   - คะแนนลบ: ตลาดคาดหวังการเติบโตสูงกว่าที่บริษัทแสดงให้เห็น
5. สร้างพอร์ต top-N ด้วยน้ำหนักเท่ากัน (equal-weight)
6. เปรียบเทียบผลตอบแทนไปข้างหน้ากับ benchmark สำหรับแต่ละระยะเวลาถือ

### กรณี Baseline vs Risk-control

Pipeline รองรับสองกลุ่มกรณีผ่าน `--case-name`:

- **Baseline** (`baseline_top5`, `baseline_top10`): Rebalance รายไตรมาสแบบ Damodaran แท้ ไม่มี stop-loss นี่คือโมเดลอ้างอิง
- **Risk-control** (`risk_control_top5_sl5`, ฯลฯ): Rebalance รายไตรมาส พร้อม stop-loss รายวัน (5% หรือ 10%) และกฎห้ามซื้อ Risk controls เป็นส่วนซ้อนแยกต่างหาก ไม่ใช่ส่วนหนึ่งของ Baseline แบบ Damodaran

ใช้ `--matrix` เพื่อสร้างทั้ง 6 กรณีในการรันเดียว

## ผลลัพธ์

- `signals.csv` — ตารางสัญญาณ cross-sectional ต่อวัน rebalance
- `portfolio_returns.csv` — ผลลัพธ์ระดับพอร์ตต่อระยะเวลาถือ
- `exclusions.csv` — หุ้นที่ถูกตัดออกและเหตุผล ต่อวัน rebalance
- `summary.csv` — ผลตอบแทนเฉลี่ย portfolio/benchmark/active และ hit rate
- `report.md` — สรุปแบบ markdown เหมาะสำหรับ thesis
- `audit_sample.csv` — ตัวอย่าง audit rows ตรวจสอบ no-lookahead
- `no_lookahead_audit.md` — สรุป audit แบบ markdown อ่านง่าย
- `manifest.json` — ข้อมูล metadata ของการรัน รวม `no_lookahead_failures`, `wacc_mode`

## การวิเคราะห์เพิ่มเติม

สร้าง sector และ WACC-sensitivity appendices:

```bash
python -m src.pipeline.backtest_analysis \
  --output-dir research_data/source_of_truth_100/backtest \
  --wacc-values 0.06 0.08 0.10 \
  --top-n 10 \
  --horizons 3 6 12 \
  --rebalance-frequency Q \
  --start-date 2020-01-01
```

ผลลัพธ์เพิ่มเติม:
- `sector_summary.csv`
- `wacc_sensitivity.csv`
- `appendix.md`

สร้างกราฟ:

```bash
python -m src.pipeline.backtest_visuals --output-dir research_data/source_of_truth_100/backtest/figures
```

กราฟที่ได้:
- `active_return_by_horizon.png`
- `hit_rate_by_horizon.png`
- `sector_active_return_heatmap.png`
- `wacc_sensitivity.png`

รวมเป็น thesis bundle:

```bash
python -m src.pipeline.thesis_bundle --output-dir research_data/source_of_truth_100/thesis_bundle
```

Bundle ประกอบด้วย:
- methodology
- ผลลัพธ์
- executive summary
- presentation script
- defense outline
- Q&A sheet
- appendix
- กราฟ
- `analysis_manifest.json`

## การตีความผล

- `Active_Return > 0` หมายถึงพอร์ตที่เลือกทำผลตอบแทนเกิน benchmark
- `Hit_Rate` คือเปอร์เซ็นต์ของช่วง rebalance ที่ผลตอบแทนพอร์ตเหนือกว่า benchmark
- `No_Lookahead_Pass` ควรเป็น `true` สำหรับทุก signal row เมื่อใช้ `--wacc-mode fixed`
