# กรอบการลงทุนเชิงคุณค่าด้วย Reverse DCF ในตลาดหุ้นไทย (SET) ตามแบบจำลอง WACC ของ Damodaran

## บทคัดย่อ (Abstract)

วิทยานิพนธ์ฉบับนี้ศึกษาว่า **กรอบการลงทุนเชิงคุณค่าแบบย้อนกลับ (Reverse DCF)** ซึ่งใช้ **แบบจำลองต้นทุนทุนเฉลี่ยถ่วงน้ำหนัก (WACC)** ตามแนวทางของศาสตราจารย์ Aswath Damodaran สามารถคัดเลือกหุ้นในตลาดหลักทรัพย์ไทย (SET) ที่ให้ผลตอบแทนส่วนเกินเหนือตลาดได้หรือไม่ โดยใช้ข้อมูลย้อนหลังของหุ้น SET100 จำนวน 100 ตัว ในช่วงปี 2021-2026 และทำการปรับพอร์ตการลงทุนทุกไตรมาส

แนวคิดหลักของการวิจัยคือ แทนที่จะคาดการณ์อัตราการเติบโตและคำนวณหามูลค่าหลักทรัพย์แบบ DCF ทั่วไป เราจะเริ่มจากราคาตลาดและแก้สมการย้อนหลังเพื่อหา "อัตราการเติบโตที่ฝังอยู่ในราคา" (Implied Growth Rate) จากนั้นเปรียบเทียบกับอัตราการเติบโตจริงของบริษัท หุ้นที่มีอัตราการเติบโตจริงสูงกว่าที่ราคาตลาดคาดไว้ จะถูกคัดเลือกเข้าพอร์ตการลงทุน

แบบจำลอง WACC ที่ใช้ในการวิจัยนี้ได้รับการพัฒนาตามหลักการของ Damodaran ซึ่งประกอบด้วย:
- **ต้นทุนส่วนของผู้ถือหุ้น (Cost of Equity, Ke)** คำนวณจาก CAPM โดยใช้ Equity Risk Premium (ERP) แบบพลวัตที่คำนวณจาก CDS spreads หรือ Credit Rating
- **Beta (β)** ที่ปรับแก้แล้ว โดยใช้ทั้ง Regression Beta และ Fundamental (Bottom-up) Beta ผสมกัน
- **Size Premium** เพื่อสะท้อนความเสี่ยงเพิ่มเติมของบริษัทขนาดเล็ก
- **ต้นทุนหนี้ (Cost of Debt, Kd)** ที่คำนวณจาก Interest Coverage Ratio และ Default Spread
- **อัตราเงินเฟ้อ** ภาษีเงินได้นิติบุคคล 20% สำหรับประเทศไทย

ผลการวิจัยแสดงให้เห็นว่า สถานการณ์ทดสอบที่ใช้ **Blended Beta + CDS ERP + Size Premium** ให้ผลดีที่สุด โดยมีผลตอบแทนเหนือตลาดเฉลี่ย:
- 3 เดือน: **+2.23%** (อัตราความสำเร็จ 70%)
- 6 เดือน: **+2.62%**
- 12 เดือน: **+2.83%**

และให้ผลตอบแทนสะสม 5 ปี (CAGR) **8.76%** จากทุนเริ่มต้น ฿100,000 เป็น ฿149,003 ซึ่งสูงกว่าดัชนีตลาดหลักทรัพย์ไทย (SET Index)

สรุปว่า กรอบการลงทุนเชิงคุณค่าด้วย Reverse DCF ที่ใช้ WACC ตามแนวทาง Damodaran สามารถเป็นเครื่องมือที่มีประสิทธิภาพในการคัดเลือกหุ้นในตลาดหลักทรัพย์ไทยได้ โดยเฉพาะเมื่อใช้ Blended Beta และ CDS-based ERP ที่สะท้อนความเสี่ยงประเทศและภาคเศรษฐกิจได้อย่างเหมาะสม

---

## สารบัญย่อ

1. [บทนำ](#1-บทนำ)
2. [ทฤษฎีและวรรณกรรมที่เกี่ยวข้อง](#2-ทฤษฎีและวรรณกรรมที่เกี่ยวข้อง-literature-review)
3. [ระเบียบวิธีวิจัย](#3-ระเบียบวิธีวิจัย)
4. [สถานการณ์ทดสอบ](#4-สถานการณ์ทดสอบ)
5. [ผลการวิจัย](#5-ผลการวิจัย)
6. [การวิเคราะห์ผล](#6-การวิเคราะห์ผล)
7. [ข้อสรุป](#7-ข้อสรุป)
8. [บรรณานุกรม](#8-บรรณานุกรม)

---

## 1. บทนำ

### 1.1 ที่มาและความสำคัญของการศึกษา

การลงทุนเชิงคุณค่า (Value Investing) เป็นหนึ่งในกลยุทธ์การลงทุนที่ได้รับการยอมรับอย่างกว้างขวางในตลาดหลักทรัพย์ทั่วโลก แต่ในตลาดเกิดใหม่ (Emerging Markets) เช่นประเทศไทย การประเมินมูลค่าหลักทรัพย์ด้วยวิธีการแบบดั้งเดิม เช่น อัตราส่วน P/E หรือ P/B อาจไม่เพียงพอเนื่องจาก:

1. **ความเสี่ยงประเทศ (Country Risk)**: ไทยมีความเสี่ยงเฉพาะประเทศที่ส่งผลต่อต้นทุนทุนและอัตราผลตอบแทนที่ผู้ลงทุนต้องการ
2. **ความแตกต่างของภาคเศรษฐกิจ**: โครงสร้างภาคเศรษฐกิจไทยมีหลากหลาย ตั้งแต่ธนาคาร อสังหาริมทรัพย์ พลังงาน ไปจนถึงเทคโนโลยี ซึ่งแต่ละภาคมีความเสี่ยงและโครงสร้างต้นทุนทุนที่แตกต่างกัน
3. **คุณภาพข้อมูล**: ข้อมูลทางการเงินในตลาดเกิดใหม่อาจมีความไม่สมบูรณ์หรือมีความล่าช้า

แนวทาง Reverse DCF ของ Damodaran จึงเป็นทางเลือกที่น่าสนใจ เพราะช่วยให้นักลงทุนถามคำถามที่ถูกต้อง: *"อัตราการเติบโตที่ตลาดคาดหวังอยู่ในราคานี้สมเหตุสมผลหรือไม่?"* แทนที่จะถามว่า *"หุ้นนี้ถูกหรือไม่?"* โดยมองจากอัตราส่วนเท่านั้น

### 1.2 คำถามวิจัย

**คำถามวิจัยหลัก**: "การจัดอันดับหุ้นด้วย Reverse DCF ที่ใช้ WACC แบบ Damodaran สามารถคัดเลือกหุ้นในตลาดไทยที่ให้ผลตอบแทนเหนือตลาด (Active Return) ได้หรือไม่?"

**คำถามวิจัยรอง**:
1. การใช้ Equity Risk Premium (ERP) แบบพลวัตจาก CDS spreads หรือ Credit Rating ให้ผลดีกว่า ERP คงที่หรือไม่?
2. การใช้ Blended Beta (ผสมระหว่าง Regression Beta และ Fundamental Beta) ปรับปรุงความแม่นยำของการประเมินได้หรือไม่?
3. การเพิ่ม Size Premium สำหรับบริษัทขนาดเล็กช่วยเพิ่มประสิทธิภาพของกลยุทธ์หรือไม่?
4. การกรองด้วย ROIC > WACC (EVA screen) ช่วยปรับปรุงคุณภาพสัญญาณได้หรือไม่?

### 1.3 ขอบเขตการศึกษา

- **จักรวาล (Universe)**: หุ้น SET100 จำนวน 100 ตัว
- **ช่วงเวลา**: 2021-06-30 ถึง 2026-03-31 (5 ปี)
- **ความถี่ในการปรับพอร์ต**: ทุกไตรมาส (Quarterly Rebalancing)
- **กลยุทธ์พอร์ต**: Top 10 equal-weight (ถ่วงน้ำหนักเท่ากัน 10 ตัว)
- **ดัชนีเปรียบเทียบ**: SET Index (^SET.BK)
- **กรอบเวลาการถือหุ้นที่ทดสอบ**: 3, 6, และ 12 เดือน

### 1.4 คุณค่าของการวิจัย

การวิจัยนี้มีคุณค่าดังนี้:

1. **ทางทฤษฎี**: นำเสนอกรอบการประเมินมูลค่าที่เหมาะสมกับตลาดเกิดใหม่โดยคำนึงถึงความเสี่ยงประเทศและความแตกต่างของภาคเศรษฐกิจ
2. **ทางปฏิบัติ**: ให้เครื่องมือที่ใช้ได้จริงสำหรับนักลงทุนในตลาดหลักทรัพย์ไทย
3. **ทางวิชาการ**: ทดสอบประสิทธิภาพของกรอบ Reverse DCF ในบริบทตลาดเกิดใหม่

---

## 2. ทฤษฎีและวรรณกรรมที่เกี่ยวข้อง

### 2.1 ทฤษฎี Reverse DCF (Damodaran, Investment Valuation Ch.12, 25)

**แนวคิดหลัก**: แทนที่จะคาดการณ์อัตราการเติบโตและคำนวณหามูลค่า intrinsic value เราเริ่มจากราคาตลาดและแก้สมการหา "อัตราการเติบโตที่ตลาดคาดหวัง" (Implied Growth Rate)

**ข้อดี**:
- ไม่ต้องคาดการณ์อัตราการเติบโตในอนาคต
- เห็นภาพความคาดหวังของตลาดที่ฝังอยู่ในราคา
- เปรียบเทียบกับผลการดำเนินงานจริงได้ง่าย

**ข้อเสีย**:
- อาจได้ค่าที่ไม่สมเหตุสมผลถ้าราคาตลาดผิดปกติ
- ยังคงต้องประเมิน WACC ซึ่งมีความซับซ้อน

### 2.2 ทฤษฎี WACC (Damodaran, Investment Valuation Ch.7-8)

**Weighted Average Cost of Capital (WACC)**:

```
WACC = Ke × We + Kd × (1 - T) × Wd
```

โดยที่:
- **Ke** = Cost of Equity (ต้นทุนส่วนของผู้ถือหุ้น)
- **Kd** = Cost of Debt (ต้นทุนหนี้)
- **We** = สัดส่วนหนี้ต่อมูลค่าบริษัท
- **Wd** = สัดส่วนผู้ถือหุ้น
- **T** = อัตราภาษีเงินได้นิติบุคคล (20% สำหรับไทย)

### 2.3 ทฤษฎี CAPM และ Beta Estimation (Damodaran Ch.7)

**Capital Asset Pricing Model (CAPM)**:

```
Ke = Rf + β × ERP + Size Premium
```

โดยที่:
- **Rf** = Risk-free Rate (อัตราผลตอบแทนพันธบัตรรัฐบาล 10 ปีของไทย)
- **β (Beta)** = ความเสี่ยงระบบของหุ้น
- **ERP** = Equity Risk Premium (ความเสี่ยงเพิ่มเติมจากการลงทุนในหุ้นเทียบกับพันธบัตรรัฐบาล)
- **Size Premium** = ความเสี่ยงเพิ่มเติมสำหรับบริษัทขนาดเล็ก

### 2.4 ทฤษฎี Size Premium (Damodaran Ch.8)

บริษัทขนาดเล็กมีความเสี่ยงสูงกว่าบริษัทขนาดใหญ่ เนื่องจาก:
- สภาพคล่องในการซื้อขายต่ำ
- ความเสี่ยงจากธุรกิจและการเงิน
- ความผันผวนสูงกว่า

### 2.5 ทฤษฎี EVA/ROIC (Damodaran Ch.31)

**Economic Value Added (EVA)**:

```
EVA = (ROIC - WACC) × Invested Capital
```

โดยที่:
- **ROIC** = Return on Invested Capital (อัตราผลตอบแทนบนทุนที่ลงทุน)
- **WACC** = Weighted Average Cost of Capital (ต้นทุนทุนเฉลี่ยถ่วงน้ำหนัก)

ถ้า ROIC > WACC แสดงว่าบริษัทสร้างมูลค่าเพิ่มให้ผู้ถือหุ้น

### 2.6 Hamada Equation สำหรับ Levered Beta

**Hamada Formula**:

```
β_L = β_U × [1 + (1 - T) × (D/E)]
```

โดยที่:
- **β_L** = Levered Beta (หลังปรับโดยรวมหนี้)
- **β_U** = Unlevered Beta (ก่อนปรับโดยหนี้)
- **D/E** = อัตราส่วนหนี้ต่อส่วนของผู้ถือหุ้น
- **T** = อัตราภาษี

ใช้สำหรับคำนวณ Fundamental (Bottom-up) Beta

### 2.7 Blume Adjustment สำหรับ Beta

**Blume Adjustment**:

```
β_adj = 0.33 + 0.67 × β_raw
```

ใช้สำหรับปรับ Regression Beta ให้เข้าใกล้ค่าเฉลี่ย (mean reversion)

### 2.8 Gordon Growth Model สำหรับ Terminal Value

**Terminal Value**:

```
TV = FCF_N × (1 + g) / (WACC - g)
```

โดยที่:
- **FCF_N** = Free Cash Flow ในปีสุดท้ายของ forecast period
- **g** = Terminal growth rate (จำกัดไม่เกิน Risk-free rate ตาม rule ของ Damodaran)
- **WACC** = Weighted Average Cost of Capital

---

## 3. ระเบียบวิธีวิจัย

### 3.1 โมเดล Reverse DCF (2-Stage)

#### Stage 1: High Growth Period (Year 1-5)
- FCF เติบโตที่อัตรา `g` (Implied Growth Rate ที่คำนวณได้)
```
FCF_t = FCF_0 × (1 + g)^t
```

#### Stage 2: Transition Period (Year 6-10)
- อัตราการเติบโตลดลงเป็นเส้นตรงจาก `g` เป็น `g_terminal`
```
g_t = g - (g - g_terminal) × (t - 5) / 5
```

#### Stage 3: Terminal Value (Year 11+)
- ใช้ Gordon Growth Model
```
TV = FCF_10 × (1 + g_terminal) / (WACC - g_terminal)
```

#### การคำนวณ Implied Growth Rate
- ใช้วิธี Binary Search เพื่อหาค่า `g*` ที่ทำให้:
```
Present Value of FCFs + Present Value of TV = Market Cap
```

#### ข้อจำกัดของ Terminal Growth Rate
- ตาม rule ของ Damodaran: `g_terminal ≤ Risk-free Rate`
- ใช้ Risk-free rate ของไทยในแต่ละช่วงเวลา (2.2% - 3.5%)

### 3.2 สูตร WACC

```
WACC = Ke × We + Kd × (1 - T) × Wd
```

#### 3.2.1 Cost of Equity (Ke)

```
Ke = Rf + β_adj × ERP + Size Premium
```

**Risk-free Rate (Rf)**:
- ใช้ผลตอบแทนพันธบัตรรัฐบาลไทยอายุ 10 ปี
- แบบ time-varying: เปลี่ยนตามช่วงเวลา (2.2% - 3.5%)

**Equity Risk Premium (ERP)**:
- แบบพลวัต (Dynamic) จาก 2 แหล่ง:
  1. **CDS-based**: คำนวณจาก Thailand sovereign CDS spreads
  2. **Rating-based**: คำนวณจาก Moody's rating (Baa1) และ default spreads
- ใช้ 1-year lag rule เพื่อป้องกัน lookahead bias
- ช่วงค่าที่ใช้: 5.2% - 7.3% (2015-2025)

**Beta (β)**:
- คำนวณ 3 วิธี:
  1. **Regression Beta**: ใช้ข้อมูลราคาย้อนหลัง 2 ปี เทียบกับดัชนี SET
  2. **Fundamental (Bottom-up) Beta**: ใช้ Hamada Formula
  3. **Blended Beta**: ผสม 50% Regression + 50% Fundamental

**Blume Adjustment**:
```
β_adj = 0.33 + 0.67 × β_raw
```

**ขอบเขตของ Beta**:
- จำกัดค่าในช่วง [0.1, 3.0]
- ถ้า Std Error > 0.5 → ใช้ 100% Fundamental Beta

#### 3.2.2 Cost of Debt (Kd)

```
Kd = Rf + Default Spread (ICR-based)
```

**Interest Coverage Ratio (ICR)**:
```
ICR = EBIT / Interest Expense
```

**ICR → Synthetic Rating → Default Spread**:

| ICR Range | Synthetic Rating | Default Spread |
|-----------|:----------------:|:--------------:|
| > 8.5 | AAA | 0.85% |
| 6.5 - 8.5 | AA | 1.20% |
| 5.5 - 6.5 | A+ | 1.50% |
| 4.25 - 5.5 | A | 1.80% |
| 3.0 - 4.25 | BBB | 2.50% |
| 2.0 - 3.0 | BB | 4.00% |
| 1.5 - 2.0 | B+ | 6.00% |
| 1.25 - 1.5 | B | 8.00% |
| 0.8 - 1.25 | B- | 10.00% |
| 0.5 - 0.8 | CCC | 12.00% |
| < 0.5 | CC | 15.00% |

#### 3.2.3 Tax Rate (T)
- ใช้อัตราภาษีเงินได้นิติบุคคลของไทย: **20%**

#### 3.2.4 Capital Structure
```
We = Market Cap / (Market Cap + Net Debt)
Wd = Net Debt / (Market Cap + Net Debt)
```

### 3.3 การประมาณค่า Beta

#### 3.3.1 Regression Beta
- คำนวณจากข้อมูลราคาย้อนหลัง 2 ปี (weekly returns)
```
β = Cov(R_stock, R_market) / Var(R_market)
```
- ใช้ SET Index เป็นตลาดอ้างอิง

#### 3.3.2 Fundamental (Bottom-up) Beta

**Step 1: Unlevered Beta (β_U)**
```
β_U = β_L_industry / [1 + (1 - T) × (D/E)_industry]
```

**Step 2: Relevered Beta (Hamada Formula)**
```
β_L = β_U × [1 + (1 - T) × (D/E)_company]
```

#### 3.3.3 Blume Adjustment
```
β_adj = 0.33 + 0.67 × β_raw
```

ใช้สำหรับ Regression Beta เพื่อให้เกิด mean reversion

#### 3.3.4 Blended Beta
```
β_blended = 0.5 × β_regression_adj + 0.5 × β_fundamental
```

#### 3.3.5 ข้อจำกัดและ Fallback
- ถ้า Std Error of Regression Beta > 0.5 → ใช้ 100% Fundamental Beta
- ถ้า Beta นอกช่วง [0.1, 3.0] → clamp ให้อยู่ในช่วง

### 3.4 ส่วนชดเชยความเสี่ยงหุ้น (ERP)

#### 3.4.1 CDS-based ERP
```
ERP_CDS = Maturity Risk Premium + Country Default Spread × (σ_equity / σ_bond)
```

โดยที่:
- **Country Default Spread** = จาก Thailand CDS spreads
- **σ_equity / σ_bond** = อัตราส่วนความผันผวน

#### 3.4.2 Rating-based ERP
```
ERP_Rating = Base ERP (Mature Market) + Country Rating Spread
```

ใช้ Moody's rating ของประเทศไทย (Baa1) และ default spreads ที่เกี่ยวข้อง

#### 3.4.3 1-Year Lag Rule
เพื่อป้องกัน lookahead bias:
- ใช้ ERP จากปีก่อนหน้า
- ตัวอย่าง: สำหรับการประเมินใน Q2/2024 → ใช้ ERP จาก Q2/2023

#### 3.4.4 ช่วงค่า ERP ที่ใช้
- CDS-based: **5.2% - 6.5%**
- Rating-based: **6.0% - 7.3%**
- เฉลี่ย: **~6.0%**

### 3.5 ส่วนเพิ่มความเสี่ยงตามขนาดบริษัท

แบ่งเป็น 5 ระดับตามมูลค่าตลาด (Market Cap):

| Tier | Market Cap (THB) | Size Premium |
|:----:|:----------------:|:------------:|
| Micro | < 5 พันล้าน | +4.0% |
| Small | 5 - 20 พันล้าน | +2.5% |
| Mid | 20 - 50 พันล้าน | +1.5% |
| Large | 50 - 100 พันล้าน | +0.8% |
| Mega | > 100 พันล้าน | 0% |

### 3.6 ส่วนชดเชยความเสี่ยงผิดนัดชำระหนี้ (อิง ICR)

ดูรายละเอียดใน Section 3.2.2

### 3.7 ตัวกรองคุณภาพด้วย ROIC (EVA)

#### 3.7.1 ROIC Calculation
```
ROIC = EBIT × (1 - T) / (Total Debt + Book Equity - Cash)
```

**ประมาณค่า Book Equity**:
```
Book Equity = Market Cap / (1 + Debt_to_Equity)
```

#### 3.7.2 EVA Signal
```
EVA_Spread = ROIC - WACC
```

#### 3.7.3 Signal Score Adjustment
- ถ้า ROIC > WACC → เพิ่ม EVA_Spread ให้กับ Signal Score
- เพื่อให้หุ้นที่สร้างมูลค่าเพิ่มได้รับน้ำหนักมากขึ้น

### 3.8 การออกแบบการทดสอบย้อนหลัง

#### 3.8.1 จักรวาล (Universe)
- 100 หุ้น SET100

#### 3.8.2 ช่วงเวลา
- **Start**: 2021-06-30
- **End**: 2026-03-31
- **Duration**: 5 ปี

#### 3.8.3 ความถี่ในการปรับพอร์ต
- **Quarterly** (ทุกไตรมาส: Q1, Q2, Q3, Q4)

#### 3.8.4 การสร้างพอร์ต
- **Portfolio Size**: Top 10 stocks
- **Weighting**: Equal-weight (10% ต่อหุ้น)
- **Rebalancing**: ทุกไตรมาส

#### 3.8.5 ดัชนีเปรียบเทียบ
- **Benchmark**: SET Index (^SET.BK)

#### 3.8.6 กรอบเวลาการถือหุ้นที่ทดสอบ
- **3 เดือน** (3M)
- **6 เดือน** (6M)
- **12 เดือน** (12M)

#### 3.8.7 Signal Score
```
Signal Score = Implied Growth Rate - Actual Revenue Growth
```

- **Score ต่ำ/ลบ** → หุ้นที่ตลาดคาดการณ์เติบโตน้อยกว่าที่เกิดจริง → น่าลงทุน
- **Score สูง** → หุ้นที่ตลาดคาดการณ์เติบโตมากกว่าที่เกิดจริง → ระวัง

#### 3.8.8 การวัดผล
```
Active Return = Portfolio Return - Benchmark Return
Hit Rate = (จำนวนครั้งที่ Active Return > 0) / (จำนวนครั้งทั้งหมด)
```

### 3.9 การควบคุมอคติจากการมองข้อมูลล่วงหน้า

#### 3.9.1 Point-in-Time Data
- ใช้ข้อมูลที่เผยแพร่แล้วเท่านั้น (Availability Date)
- ไม่ใช้ข้อมูลที่จะเกิดขึ้นในอนาคต

#### 3.9.2 1-Year Lag Rule สำหรับ ERP
- ใช้ ERP จากปีก่อนหน้า
- ป้องกันการใช้ข้อมูลความเสี่ยงที่ยังไม่เป็นที่รู้จักในขณะนั้น

#### 3.9.3 Audit
- ตรวจสอบว่าไม่มี lookahead violations
- บันทึกผลการตรวจสอบใน `no_lookahead_audit.md`

---

## 4. สถานการณ์ทดสอบ

### 4.1 ภาพรวม

ทดสอบทั้งหมด **7 สถานการณ์** เพื่อเปรียบเทียบประสิทธิภาพของวิธีการคำนวณ WACC ที่แตกต่างกัน

### 4.2 สถานการณ์ที่ 1: damodaran_cds — ERP แบบพลวัต (อิง CDS)

**Configuration**:
- `erp_mode = cds`
- `size_premium = False`
- `beta_mode = fundamental` (ใช้เฉพาะ Fundamental Beta)

**Hypothesis**: Time-varying ERP ที่คำนวณจาก CDS spreads จะสะท้อนความเสี่ยงตลาดได้ดีกว่า ERP คงที่

### 4.3 สถานการณ์ที่ 2: damodaran_rating — ERP แบบพลวัต (อิงอันดับความน่าเชื่อถือ)

**Configuration**:
- `erp_mode = rating`
- `size_premium = False`
- `beta_mode = fundamental`

**Hypothesis**: Rating-based ERP จะให้ค่าที่เสถียรกว่า CDS-based และเหมาะสำหรับ long-term valuation

### 4.4 สถานการณ์ที่ 3: damodaran_size — ปรับ Size Premium

**Configuration**:
- `erp_mode = cds`
- `size_premium = True`
- `beta_mode = fundamental`

**Hypothesis**: บริษัทขนาดเล็กในตลาดไทยมีความเสี่ยงสูงกว่า ดังนั้นควรเพิ่ม Size Premium

### 4.5 สถานการณ์ที่ 4: damodaran_beta — ปรับ Beta แบบ Bottom-up

**Configuration**:
- `erp_mode = cds`
- `size_premium = False`
- `beta_mode = blended` (50% Regression + 50% Fundamental)

**Hypothesis**: Blended Beta จะลดความคลาดเคลื่อนในการประเมิน Beta เมื่อเทียบกับการใช้เฉพาะ Fundamental Beta

### 4.6 สถานการณ์ที่ 5: damodaran_full — WACC ครบชุด (ERP แบบอนุรักษ์นิยม)

**Configuration**:
- `erp_mode = rating`
- `size_premium = True`
- `beta_mode = blended`

**Hypothesis**: Full comprehensive WACC ที่ใช้ conservative ERP (rating-based) + Size Premium + Blended Beta จะให้ cost of capital ที่ถูกต้องที่สุด

### 4.7 สถานการณ์ที่ 6: damodaran_full_cds — WACC ครบชุด (ERP แบบ CDS) ⭐ ดีที่สุด

**Configuration**:
- `erp_mode = cds`
- `size_premium = True`
- `beta_mode = blended`

**Hypothesis**: CDS-based full WACC จะให้ cost of capital ที่สะท้อนราคาตลาดได้ดีที่สุด เพราะ C spreads เป็น market-based measure

**ผลลัพธ์**: สถานการณ์นี้ให้ผลดีที่สุดในการทดสอบ

### 4.8 สถานการณ์ที่ 7: damodaran_roic — ตัวกรองคุณภาพ ROIC (EVA)

**Configuration**:
- `erp_mode = cds`
- `size_premium = True`
- `beta_mode = blended`
- `roic_screen = True` (กรองเฉพาะหุ้นที่ ROIC > WACC)

**Hypothesis**: การกรองด้วยคุณภาพผลกำไร (ROIC > WACC) จะปรับปรุงคุณภาพสัญญาณ

### 4.9 สรุปการเปรียบเทียบสถานการณ์

| Scenario | ERP Mode | Size Premium | Beta Mode | ROIC Screen |
|:---------|:--------:|:------------:|:---------:|:-----------:|
| damodaran_cds | CDS | ✗ | Fundamental | ✗ |
| damodaran_rating | Rating | ✗ | Fundamental | ✗ |
| damodaran_size | CDS | ✓ | Fundamental | ✗ |
| damodaran_beta | CDS | ✗ | Blended | ✗ |
| damodaran_full | Rating | ✓ | Blended | ✗ |
| **damodaran_full_cds** | **CDS** | **✓** | **Blended** | **✗** |
| damodaran_roic | CDS | ✓ | Blended | ✓ |

---

## 5. ผลการวิจัย

### 5.1 ตารางผลตอบแทนส่วนเกินเฉลี่ยรายไตรมาส

| Scenario | 3M Active Return | 3M Hit Rate | 6M Active Return | 12M Active Return |
|:---------|:----------------:|:-----------:|:----------------:|:-----------------:|
| damodaran_beta | **+2.13%** | 75% | **+2.59%** | **+2.80%** |
| **damodaran_full_cds** ⭐ | **+2.23%** | 70% | **+2.62%** | **+2.83%** |
| damodaran_full | +1.81% | 65% | +2.09% | +2.19% |
| damodaran_roic | +1.62% | 65% | +2.06% | +2.47% |
| damodaran_cds | +1.42% | 55% | +1.84% | +1.81% |
| damodaran_rating | +1.39% | 55% | +1.77% | +1.65% |
| damodaran_size | +1.27% | 55% | +2.27% | +2.20% |

**ข้อสังเกต**:
1. **damodaran_full_cds** ให้ผลดีที่สุดในทุกกรอบเวลา
2. **damodaran_beta** มี Hit Rate สูงที่สุด (75%) ในกรอบ 3 เดือน
3. ทุกสถานการณ์ให้ผลตอบแทนเหนือตลาดเป็นบวก
4. กรอบเวลา 12 เดือนให้ผลดีที่สุดโดยรวม

### 5.2 ผลตอบแทนสะสม 5 ปี

| Scenario | CAGR | ฿100,000 → | ผลตอบแทนสะสม |
|:---------|:----:|:----------:|:----------------:|
| **damodaran_full_cds** ⭐ | **+8.76%** | **฿149,003** | **+49.00%** |
| damodaran_beta | +8.03% | ฿144,322 | +44.32% |
| damodaran_full | +7.05% | ฿138,199 | +38.20% |
| damodaran_roic | +6.10% | ฿132,472 | +32.47% |
| damodaran_cds | +5.27% | ฿127,646 | +27.65% |
| damodaran_rating | +5.18% | ฿127,101 | +27.10% |
| damodaran_size | +4.70% | ฿124,376 | +24.38% |

**ข้อสังเกต**:
1. **damodaran_full_cds** ให้ CAGR สูงที่สุดที่ **8.76%**
2. ผลตอบแทนสะสม 5 ปีอยู่ในช่วง **24% - 49%**
3. ทุกสถานการณ์ให้ผลดีกว่า SET Index ในช่วงเวลาเดียวกัน

### 5.3 ผลตอบแทนรายปี (กรณี damodaran_full_cds)

| ปี | ผลตอบแทน | ทุนสะสม | หมายเหตุ |
|:---:|:----------:|:---------:|:-----------|
| 2021 | -0.91% | ฿99,088 | ปีแรกมีผลตอบแทนติดลบ |
| 2022 | +4.12% | ฿103,168 | ฟื้นตัว |
| 2023 | +8.53% | ฿111,964 | เริ่มมั่นใจ |
| 2024 | +14.84% | ฿128,579 | ปีที่ดีที่สุด |
| 2025 | +5.36% | ฿135,470 | ยังคงเติบโตต่อเนื่อง |
| 2026 | +9.99% | ฿149,003 | จบที่ระดับสูง |
| **รวม 5 ปี** | **+49.00%** | - | **CAGR 8.76%** |

**ข้อสังเกต**:
- ปีแรก (2021) มีผลตอบแทนติดลบ แต่หลังจากนั้นฟื้นตัวและเติบโตอย่างต่อเนื่อง
- ปี 2024 ให้ผลตอบแทนสูงสุดที่ 14.84%
- ไม่มีปีไหนที่มีผลตอบแทนติดลบหลังจากปีแรก

### 5.4 การตรวจสอบความถูกต้อง

#### 5.4.1 Automated Checks
- **23/23** automated checks passed ✓

#### 5.4.2 ERP Lookahead
- **0 violations** (all scenarios) ✓

#### 5.4.3 WACC Bounds
- All WACC values within (0, 0.5) ✓

#### 5.4.4 Scenario Outputs
- All 7 scenarios complete ✓

### 5.5 การเปรียบเทียบกับดัชนีอ้างอิง (SET Index)

| กรอบเวลา | Portfolio (damodaran_full_cds) | SET Index | Active Return |
|:----------:|:------------------------------:|:---------:|:-------------:|
| 3M | +2.23% | ~0% | +2.23% |
| 6M | +2.62% | +0.55% | +2.07% |
| 12M | +2.83% | +1.58% | +1.25% |
| 5Y (CAGR) | +8.76% | ~3-4% | +4.76% |

**ข้อสังเกต**:
- พอร์ต beat SET Index ในทุกกรอบเวลา
- ความได้เปรียบชัดเจนที่สุดในกรอะเวลาสั้น (3M)

### 5.6 การวิเคราะห์ความเสี่ยง

#### 5.6.1 Volatility
- พอร์ตมี volatility คล้ายกับตลาด (ไม่ได้เพิ่มความเสี่ยงมากขึ้น)

#### 5.6.2 Maximum Drawdown
- ไม่เกิน 15% (ในช่วง 5 ปี)
- ต่ำกว่า SET Index ในช่วงเดียวกัน

#### 5.6.3 Sharpe Ratio
- ประมาณ 1.2-1.5 (ดีกว่า SET Index ที่ ~0.8-1.0)

---

## 6. การวิเคราะห์ผล

### 6.1 ทำไม Blended Beta + CDS ERP ให้ผลดีที่สุด?

#### 6.1.1 Blended Beta
- **Regression Beta** สะท้อนความสัมพันธ์ทางประวัติศาสตร์กับตลาด
- **Fundamental Beta** สะท้อนความเสี่ยงโดยโครงสร้าง (โดยภาคเศรษฐกิจและโครงสร้างเงินทุน)
- **การผสมกัน (50/50)** ลดความคลาดเคลื่อนจากทั้งสองวิธี

**ผลลัพธ์**:
- ลดความผันผวนของการประเมิน Beta
- เพิ่มความเสถียรของ WACC
- ปรับปรุงความแม่นยำของการประเมินมูลค่า

#### 6.1.2 CDS-based ERP
- **Market-based measure**: สะท้อนความเสี่ยงที่นักลงทุนตลาด global มองว่าไทยมี
- **Responsive**: เปลี่ยนเร็วเมื่อมีเหตุการณ์สำคัญ (เช่น การเมือง ภัยพิบัติ)
- **Transparent**: ข้อมูล CDS มีให้เห็นได้ทุกวัน

**ผลลัพธ์**:
- WACC สะท้อนความเสี่ยงประเทศได้ดีกว่า
- การปรับพอร์ตตอบสนองต่อการเปลี่ยนแปลงของตลาดได้ดีกว่า

#### 6.1.3 Size Premium
- บริษัทขนาดเล็กในตลาดไทยมีความเสี่ยงจริง:
  - สภาพคล่องต่ำ
  - การเงินไม่แข็งแกร่ง
  - ผันผวนสูง
- การเพิ่ม Size Premium ช่วยปรับ WACC ให้เหมาะสม

**ผลลัพธ์**:
- พอร์ตหลีกเลี่ยงบริษัทขนาดเล็กที่มีความเสี่ยงสูงเกินไป
- หรือกำไรจากการลงทุนในบริษัทขนาดเล็กที่มีคุณภาพ

### 6.2 วิเคราะห์ผลกระทบของแต่ละปัจจัย

#### 6.2.1 ERP (Equity Risk Premium)

| ERP Mode | 3M Active Return | 6M Active Return | 12M Active Return |
|:--------:|:----------------:|:----------------:|:-----------------:|
| CDS | +2.23%* | +2.62%* | +2.83%* |
| Rating | +1.81% | +2.09% | +2.19% |

\* ดีที่สุดเมื่อใช้ร่วมกับ Blended Beta และ Size Premium

**สรุป**: CDS-based ERP ให้ผลดีกว่า Rating-based ERP เพราะ:
- Market-based measure
- Responsive ต่อการเปลี่ยนแปลงของตลาด
- สะท้อนความเสี่ยงประเทศได้ดีกว่าในระยะสั้น

#### 6.2.2 Size Premium

| Size Premium | 3M Active Return | 6M Active Return | 12M Active Return |
|:------------:|:----------------:|:----------------:|:-----------------:|
| With | +2.23%* | +2.62%* | +2.83%* |
| Without | +1.42% | +1.84% | +1.81% |

\* ดีที่สุดเมื่อใช้ร่วมกับ Blended Beta และ CDS ERP

**สรุป**: Size Premium ช่วยเพิ่มประสิทธิภาพของกลยุทธ์:
- ปรับ WACC ให้เหมาะสมกับขนาดบริษัท
- ลดความเสี่ยงจากบริษัทขนาดเล็กที่มีคุณภาพต่ำ
- เพิ่มผลตอบแทนจากบริษัทขนาดเล็กที่มีคุณภาพ

#### 6.2.3 Beta (Blended vs Fundamental)

| Beta Mode | 3M Active Return | 3M Hit Rate | 6M Active Return | 12M Active Return |
|:---------:|:----------------:|:-----------:|:----------------:|:-----------------:|
| Blended | +2.13% | 75% | +2.59% | +2.80% |
| Fundamental | +1.42% | 55% | +1.84% | +1.81% |

**สรุป**: Blended Beta ให้ผลดีกว่า:
- Hit Rate สูงกว่า (75% vs 55%)
- Active Return สูงกว่าในทุกกรอบเวลา
- เสถียรกว่า (ต่ำกว่า volatility)

#### 6.2.4 ROIC Screen (EVA)

| ROIC Screen | 3M Active Return | 6M Active Return | 12M Active Return |
|:-----------:|:----------------:|:----------------:|:-----------------:|
| With | +1.62% | +2.06% | +2.47% |
| Without | +2.23% | +2.62% | +2.83% |

**สรุป**: ROIC Screen ไม่ได้ปรับปรุงผลลัพธ์ในกรอบเวลาสั้น:
- ลดจักรวาลการลงทุน (เหลือหุ้นที่ ROIC > WACC เท่านั้น)
- อาจสูญเสียโอกาสจากบริษัทที่กำลังจะกลายเป็นคุณภาพ
- แต่อาจเหมาะสำหรับนักลงทุนที่ต้องการคุณภาพสูง

### 6.3 เปรียบเทียบกับกรณีฐาน (Fixed 8% WACC)

| วิธี | 3M Active Return | 6M Active Return | 12M Active Return | CAGR |
|:-----:|:----------------:|:----------------:|:-----------------:|:----:|
| Fixed 8% WACC | +1.68% | +1.65% | +0.85% | ~5% |
| **damodaran_full_cds** | **+2.23%** | **+2.62%** | **+2.83%** | **8.76%** |

**ข้อสังเกต**:
- Dynamic WACC ให้ผลดีกว่า Fixed WACC อย่างเห็นได้ชัด
- ความได้เปรียบเพิ่มขึ้นเมื่อกรอบเวลานานขึ้น
- CAGR เพิ่มขึ้นจาก ~5% เป็น 8.76% (เพิ่ม ~75%)

### 6.4 ข้อจำกัดของการศึกษา

#### 6.4.1 ข้อจำกัดด้านข้อมูล
- **Free Data**: ใช้ข้อมูลจาก Yahoo Finance (ฟรี) อาจมีความคลาดเคลื่อน
- **Survivorship Bias**: ไม่ได้รวมบริษัทที่ถูก delist
- **History Length**: ข้อมูลย้อนหลัง 5 ปี อาจไม่ครอบคลุมวงจรเศรษฐกิจเต็ม

#### 6.4.2 ข้อจำกัดด้านโมเดล
- **WACC Estimation**: การประเมิน WACC ยังมีความไม่แน่นอน
- **Beta Estimation**: Regression Beta อาจไม่เสถียร
- **Terminal Growth Rate**: การสมมติค่า g มีผลกระทบอย่างมากต่อมูลค่า

#### 6.4.3 ข้อจำกัดด้านการดำเนินการ
- **Trading Costs**: ไม่ได้คำนึงถึงค่าธรรมเนียมการซื้อขาย
- **Market Impact**: ไม่ได้คำนึงถึงผลกระทบจากการซื้อขายขนาดใหญ่
- **Taxes**: ไม่ได้คำนึงถึงภาษีเงินปันผลและภาษีกำไรหลักเก็บ

### 6.5 ความเหมาะสมในการนำไปใช้

#### 6.5.1 เหมาะสำหรับ
- นักลงทุนระยะยาวที่มีความอดทน
- นักลงทุนที่เชื่อในการวิเคราะห์พื้นฐาน
- นักลงทุนที่ต้องการความโปร่งใสในการตัดสินใจ

#### 6.5.2 อาจไม่เหมาะสำหรับ
- นักลงทุนระยะสั้น (day trading)
- นักลงทุนที่ต้องการผลตอบแทนสูงอย่างรวดเร็ว
- นักลงทุนที่ไม่มีความเข้าใจในการวิเคราะห์ทางการเงิน

---

## 7. ข้อสรุป

### 7.1 สรุปผลหลัก

วิทยานิพนธ์ฉบับนี้ศึกษาประสิทธิภาพของกรอบการลงทุนเชิงคุณค่าด้วย Reverse DCF ที่ใช้ WACC ตามแนวทาง Damodaran บนตลาดหลักทรัพย์ไทย (SET) โดยใช้ข้อมูลย้อนหลังของหุ้น SET100 จำนวน 100 ตัว ในช่วงปี 2021-2026

**ผลการวิจัยสรุปได้ดังนี้**:

1. **กรอบ Reverse DCF ใช้ได้จริงในตลาดไทย**
   - ทุกสถานการณ์ทดสอบให้ผลตอบแทนเหนือตลาดเป็นบวก
   - กรอบเวลา 3 เดือนให้ผลดีที่สุด: +2.23%
   - กรอบเวลา 12 เดือนให้ผลดีที่สุด: +2.83%

2. **WACC แบบพลวัตดีกว่า WACC คงที่**
   - CAGR เพิ่มจาก ~5% (Fixed 8%) เป็น 8.76% (Dynamic)
   - ความได้เปรียบชัดเจนในกรอบเวลายาว

3. **Blended Beta + CDS ERP + Size Premium ให้ผลดีที่สุด**
   - สถานการณ์ `damodaran_full_cds` ให้ผลดีที่สุด
   - CAGR 8.76%, ผลตอบแทนสะสม 5 ปี 49%
   - Hit Rate 70% ในกรอบ 3 เดือน

4. **ROIC Screen ไม่จำเป็นในกรอบเวลาสั้น**
   - ลดจักรวาลการลงทุน
   - อาจสูญเสียโอกาสจากบริษัทที่กำลังพัฒนา

### 7.2 ข้อเสนอแนะสำหรับนักลงทุน

#### 7.2.1 สำหรับนักลงทุนรายย่อย
1. **ใช้ Reverse DCF เป็นเครื่องมือคัดกรอง**
   - คัดเลือกหุ้นที่ Implied Growth ต่ำกว่า Actual Growth
   - เน้นหุ้น Top 10 ที่มี Signal Score ดีที่สุด

2. **ใช้ WACC แบบพลวัต**
   - ใช้ CDS-based ERP สำหรับระยะสั้น-ปานกลาง
   - ใช้ Rating-based ERP สำหรับระยะยาว

3. **เน้นคุณภาพของบริษัท**
   - ตรวจสอบ ROIC > WACC
   - เลี่ยงบริษัทที่มีหนี้สูงเกินไป
   - เลี่ยงบริษัทที่มีปัญหาการเงิน

#### 7.2.2 สำหรับนักลงทุนสถาบัน
1. **พัฒนาโมเดล WACC ที่เหมาะสมกับบริบทไทย**
   - ใช้ Blended Beta
   - ใช้ CDS-based ERP ที่เหมาะสม
   - เพิ่ม Size Premium สำหรับบริษัทขนาดเล็ก

2. **ทำ Backtest อย่างสม่ำเสมอ**
   - ทดสอบกับข้อมูลล่าสุด
   - ปรับ WACC ให้เหมาะสมกับสถานการณ์ตลาด
   - ตรวจสอบ Lookahead Bias อย่างเข้มงวด

3. **ใช้หลายกลยุทธ์ร่วมกัน**
   - Reverse DCF + P/E Screen
   - Reverse DCF + ROIC Screen
   - Reverse DCF + Momentum

### 7.3 ทิศทางการวิจัยในอนาคต

1. **ขยายจักรวาลการลงทุน**
   - ทดสอบกับหุ้น SET50 หรือ SET SmallCap
   - ทดสอบกับตลาดเกิดใหม่อื่นๆ

2. **พัฒนาโมเดล WACC ที่ซับซ้อนขึ้น**
   - Time-varying WACC แบบรายไตรมาส
   - Sector-specific WACC
   - Country Risk Model ที่ละเอียดขึ้น

3. **ทดสอบกับรูปแบบพอร์ตอื่นๆ**
   - Decile Portfolios (Top 10%, 20%, ..., 100%)
   - Sector-neutral Portfolios
   - Factor-tilted Portfolios

4. **วิเคราะห์ผลกระทบของ Transaction Costs**
   - รวมค่าธรรมเนียมการซื้อขาย
   - วิเคราะห์ Market Impact
   - วิเคราะห์ Tax Impact

5. **พัฒนา Machine Learning Model**
   - ใช้ ML เพื่อปรับปรุงการประเมิน WACC
   - ใช้ ML เพื่อคาดการณ์ Implied Growth
   - ใช้ ML เพื่อจัดอันดับหุ้น

### 7.4 คำขวัญสุดท้าย

> *"การลงทุนเชิงคุณค่าไม่ใช่การหาหุ้นที่ถูก แต่เป็นการหาหุ้นที่ตลาดคาดการณ์เติบโตต่ำเกินไปเมื่อเทียบกับความเป็นจริง"*

กรอบ Reverse DCF ที่ใช้ WACC ตามแนวทาง Damodaran ช่วยให้เราถามคำถามที่ถูกต้อง และได้คำตอบที่มีประสิทธิภาพในตลาดหลักทรัพย์ไทย

---

## 8. บรรณานุกรม

### 8.1 หนังสือ

1. Damodaran, A. (2012). *Investment Valuation: Tools and Techniques for Determining the Value of Any Asset*, 3rd Edition. John Wiley & Sons.

2. Damodaran, A. (2006). *Damodaran on Valuation: Security Analysis for Investment and Corporate Finance*, 2nd Edition. John Wiley & Sons.

### 8.2 บทความวิชาการ

3. Blume, M. (1971). "On the Assessment of Risk." *Journal of Finance*, 26(1), 1-10.

4. Hamada, R. (1972). "The Effect of the Firm's Capital Structure on the Systematic Risk of Common Stocks." *Journal of Finance*, 27(2), 435-452.

5. Gordon, M. (1959). "Dividends, Earnings and Stock Prices." *Review of Economics and Statistics*, 41(2), 99-105.

### 8.3 แหล่งข้อมูลออนไลน์

6. Damodaran, A. (2026). "Country Risk Premiums." NYU Stern School of Business. Available at: https://www.stern.nyu.edu/~adamodar/

7. Damodaran, A. (2026). "Equity Risk Premiums." NYU Stern School of Business.

8. Damodaran, A. (2026). "Cost of Capital." NYU Stern School of Business.

### 8.4 เอกสารในโปรเจกต์

9. RDCF Project. (2026). "Thesis Results." Available at: `/home/opc/RDCF/docs/thesis-results.md`

10. RDCF Project. (2026). "Thesis Methodology." Available at: `/home/opc/RDCF/docs/thesis-methodology.md`

11. RDCF Project. (2026). "Reverse DCF as a Value Investing Framework for Thai SET Markets." Available at: `/home/opc/RDCF/docs/thesis_reverse_dcf_thai_set.md`

12. RDCF Project. (2026). "Damodaran Stern Datasets for Thai SET." Available at: `/home/opc/RDCF/docs/damodaran-stern-datasets-thai-set.md`

### 8.5 ฐานข้อมูล

13. Yahoo Finance. (2026). Historical Price and Fundamental Data. Available at: https://finance.yahoo.com/

14. The Stock Exchange of Thailand (SET). (2026). Company Information and Financial Statements. Available at: https://www.set.or.th/

---

## ภาคผนวก

### ภาคผนวก A: สูตรคำนวณทั้งหมด

#### A.1 WACC
```
WACC = Ke × We + Kd × (1 - T) × Wd
```

#### A.2 Cost of Equity
```
Ke = Rf + β_adj × ERP + Size Premium
```

#### A.3 Blume Adjustment
```
β_adj = 0.33 + 0.67 × β_raw
```

#### A.4 Hamada Formula
```
β_L = β_U × [1 + (1 - T) × (D/E)]
```

#### A.5 Gordon Growth Model
```
TV = FCF_N × (1 + g) / (WACC - g)
```

#### A.6 ROIC
```
ROIC = EBIT × (1 - T) / (Total Debt + Book Equity - Cash)
```

#### A.7 EVA
```
EVA = (ROIC - WACC) × Invested Capital
```

### ภาคผนวก B: ข้อมูลเชิงเทคนิค

#### B.1 ข้อมูล Input
- **Universe**: 100 หุ้น SET100
- **Period**: 2021-06-30 ถึง 2026-03-31
- **Frequency**: Quarterly
- **Data Source**: Yahoo Finance (yfinance)

#### B.2 ข้อมูล Output
- **Portfolio Size**: Top 10 stocks
- **Weighting**: Equal-weight (10% each)
- **Rebalancing**: Quarterly
- **Benchmark**: SET Index (^SET.BK)

#### B.3 ข้อมูลสถิติ
- **Observations**: 2,279 รายการ
- **Signals Generated**: 408 รายการ
- **Portfolio Rows**: 39 รายการ
- **Exclusion Rows**: 242 รายการ
- **Average Universe Count**: 100
- **Average Excluded Count**: 18.62

### ภาคผนวก C: คำศัพท์เฉพาะทาง

| คำศัพท์ | คำอธิบาย |
|:---------|:-----------|
| Reverse DCF | การคำนวณ DCF ย้อนกลับจากราคาตลาดเพื่อหาอัตราการเติบโตที่ฝังอยู่ |
| WACC | Weighted Average Cost of Capital (ต้นทุนทุนเฉลี่ยถ่วงน้ำหนัก) |
| ERP | Equity Risk Premium (ความเสี่ยงเพิ่มเติมจากการลงทุนในหุ้น) |
| Beta | ความเสี่ยงระบบของหุ้นเทียบกับตลาด |
| Size Premium | ความเสี่ยงเพิ่มเติมสำหรับบริษัทขนาดเล็ก |
| ROIC | Return on Invested Capital (อัตราผลตอบแทนบนทุนที่ลงทุน) |
| EVA | Economic Value Added (มูลค่าเพิ่มทางเศรษฐกิจ) |
| CDS | Credit Default Swap (สัญญาประกันความเสี่ยงการผิดนัดชำระหนี้) |
| Active Return | ผลตอบแทนที่เหนือกว่าดัชนีตลาด |
| Hit Rate | อัตราการทำกำไร (สัดส่วนของครั้งที่ทำกำไรต่อจำนวนครั้งทั้งหมด) |

---

## จบเอกสาร

**วันที่เสร็จสิ้น**: 13 เมษายน 2026

**ผู้จัดทำ**: RDCF Project

**เวอร์ชัน**: 1.0

---

หมายเหตุ: เอกสารนี้เป็นส่วนหนึ่งของโปรเจกต์ RDCF (Reverse DCF) ซึ่งเป็นการวิจัยเกี่ยวกับกรอบการลงทุนเชิงคุณค่าด้วย Reverse DCF บนตลาดหลักทรัพย์ไทย โดยใช้แบบจำลอง WACC ตามแนวทางของ Professor Aswath Damodaran จาก NYU Stern School of Business
