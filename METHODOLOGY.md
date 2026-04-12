# 📚 Reverse DCF Methodology Explained

## หลักการทางทฤษฎี

### 1. คืออะไร?

**Reverse DCF** = กลับ DCF จากปกติ

**DCF ปกติ:**
```
Input: Growth Rate
Process: Calculate FCF projections
Output: Intrinsic Value
```

**Reverse DCF:**
```
Input: Market Price
Process: Back-solve for Growth Rate
Output: Implied Growth Rate
```

---

### 2. ทำไมต้อง Reverse DCF?

#### ปัญหา DCF ปกติ:
```
คุณ: "ผมคิดว่า A จะโต 10% ต่อปี"
DCF: "งั้นมูลค่า 100 บาท"
คุณ: "แต่ตลาดราคา 150 บาท ตลาดผิดรึเปล่า?"
```

#### คำตอบ Reverse DCF:
```
Market: "ราคา 150 บาท"
Reverse DCF: "งั้นตลาดคาดว่า A จะโต 18% ต่อปี"
คุณ: "โอ้ 18% สูงเกินไป ผมคิดว่าแค่ 10%"
คุณ: "แปลว่าตลาด Overvalued → ขาย"
```

**ข้อดี:**
- ✅ ไม่ต้อง guess growth rate
- ✅ เห็นว่าตลาด **คาดการณ์** อะไร
- ✅ เปรียบเทียบกับความคิดเราได้

---

### 3. สูตรทางคณิตศาสตร์

#### สูตร DCF มาตรฐาน:
```
Intrinsic Value = Σ (FCF_t / (1 + WACC)^t) + Terminal Value

Terminal Value = FCF_n × (1 + g) / (WACC - g)
```

#### Reverse DCF Process:

**Step 1: Setup Equation**
```
Market Price = f(growth_rate)
```

**Step 2: Solve for Growth Rate**
```
Use iterative method (Binary Search)

Low: -10% (decline)
High: +50% (hyper growth)

Repeat:
  Mid = (Low + High) / 2
  Calculate Intrinsic Value using Mid as growth
  If Intrinsic > Market Price:
    High = Mid  (growth too high)
  Else:
    Low = Mid   (growth too low)

Until: |Intrinsic - Market| < tolerance
```

---

### 4. Components สำคัญ

#### 4.1 Free Cash Flow (FCF)
```python
FCF = Operating Cash Flow - Capital Expenditures
```

**Why FCF?**
- Cash ที่เอาจริงได้
- ไม่ใช่ Accounting profit
- ใช้จ่าย dividend ได้

#### 4.2 WACC (Weighted Average Cost of Capital)
```python
WACC = (E/V) × Re + (D/V) × Rd × (1 - Tax Rate)

Where:
E = Equity Value
D = Debt Value
V = Total Value (E + D)
Re = Cost of Equity (CAPM)
Rd = Cost of Debt
```

**Cost of Equity (CAPM):**
```python
Re = Rf + β × (Rm - Rf)

Where:
Rf = Risk-free rate (Thai bond ~3.5%)
β = Beta (stock volatility vs market)
Rm - Rf = Market risk premium (~6% for emerging market)
```

#### 4.3 Terminal Growth Rate
```python
Terminal Growth = Long-term GDP Growth = 2.5%
```

**Why 2.5%?**
- ไม่มีบริษัทโตเร็วกว่าประเทศไปนานๆ
- 2.5% ≈ จีดีพีไทย long-term

---

### 5. Growth Differential Analysis

#### Formula:
```python
Growth Differential = Implied Growth - Actual Growth
```

#### Interpretation:

**Scenario 1: Negative Differential (-)**
```
Implied: 3%
Actual: 5%
Differential: -2%

Meaning: ตลาดคาดต่ำกว่าความเป็นจริง
Action: Opportunity (ตลาดมองข้าม)
```

**Scenario 2: Positive Differential (+)**
```
Implied: 10%
Actual: 5%
Differential: +5%

Meaning: ตลาดคาดสูงกว่าความเป็นจริง
Action: Caution (ตลาดใฝ่ฝัน)
```

---

### 6. Sensitivity Analysis

#### ความ sensitive ของแต่ละ input:

| Input | Impact | เมื่อเปลี่ยน 1% |
|-------|--------|-------------------|
| **Growth Rate** | สูงมาก | Value เปลี่ยน 15-20% |
| **WACC** | สูง | Value เปลี่ยน 10-15% |
| **Terminal Growth** | ปานกลาง | Value เปลี่ยน 5-10% |
| **Initial FCF** | ปานกลาง | Value เปลี่ยน 8-12% |

#### Key Insight:
> **Garbage In, Garbage Out**
>
> ถ้า Input ผิด → Output ก็ผิด
> ดังนั้นต้องใช้ good judgment ประกอบ

---

### 7. Limitations & Edge Cases

#### ❌ ไม่เหมาะกับ:

**1. Growth Stocks (Unprofitable)**
```
Problem: FCF < 0 หรือใกล้ 0
Result: Implied Growth สูงผิดปกติ (50%+)
Solution: ใช้ Revenue-based model แทน
```

**2. Turnaround Stories**
```
Problem: Past growth < 0 แต่ future > 0
Result: Model ใช้ historical data
Solution: Adjust input manually
```

**3. Highly Cyclical**
```
Problem: FCF volatile (e.g., commodities)
Result: Single year FCF ไม่ representative
Solution: Average 3-5 years
```

**4. Financials (Banks)**
```
Problem: FCF concept ไม่ชัดเจน
Result: ต้อง adjust model
Solution: ใช้ Dividend Discount Model
```

#### ✅ เหมาะกับ:

- ✅ Mature businesses
- ✅ Stable FCF
- ✅ Predictable growth
- ✅ Non-cyclical

---

### 8. Best Practices

#### Do's:
1. ✅ ใช้ **multiple scenarios** (Base, Bull, Bear)
2. ✅ เปรียบเทียบกับ **peers**
3. ✅ Look at **history** (Is implied growth reasonable?)
4. ✅ Combine with **qualitative** analysis
5. ✅ Update **regularly** (Quarterly)

---

### Datasource policy for this repo

- **Primary datasource**: Yahoo Finance via `yfinance`
- **Why**: free, scriptable, reusable, และ practical กว่าสำหรับงาน backtest
- **Official SET pages**: ใช้สำหรับ **optional manual validation** ไม่ใช่ main pipeline
- **Free-data tradeoff rule**: ถ้าความสดใหม่กับความครบถ้วนย้อนหลังขัดกัน ให้เลือก datasource ที่ทำให้ **backtest แข็งแรงกว่า**
- **Research dataset bundle**: ใช้ `python -m rdcf.data_pipeline` เพื่อสร้าง snapshot fundamentals + historical statement observations + historical prices + benchmark history + manifest สำหรับงาน backtest
- **Availability assumption**: ใช้ `Statement_Date + reporting lag` เป็น availability date แบบโปร่งใสและต้อง report เป็น assumption ในงาน thesis

#### Don'ts:
1. ❌ อย่าพึ่งพาตัวเลขอย่างเดียว
2. ❌ อย่าลืม **margin of safety**
3. ❌ อย่าลืม **qualitative factors**
4. ❌ อย่าใช้กับ **unprofitable** companies
5. ❌ อย่า forget to **sanity check**

---

### 9. Example Walkthrough

#### Stock: Bangkok Bank (BBL.BK)

**Inputs:**
```
Current Price: 162.50 ฿
Market Cap: 450,000M ฿
FCF: 45,000M ฿
WACC: 8.5%
Shares: 2,770M
```

**Reverse DCF Calculation:**
```
Step 1: Enterprise Value = 450,000M

Step 2: PV of FCFs (10 years)
  Year 1-5: Growth = ?
  Year 6-10: Growth declines to 2.5%

Step 3: Terminal Value = FCF10 × 1.025 / (0.085 - 0.025)

Step 4: Solve for Growth that makes:
  PV(FCFs) + PV(Terminal) = 450,000M

Result: Implied Growth = 3.2%
```

**Interpretation:**
```
Actual Revenue Growth: 5.1%
Implied Growth: 3.2%
Differential: -1.9%

Conclusion: Market is too pessimistic
Action: Undervalued → Buy
```

---

### 10. Advanced Topics

#### Margin of Safety:
```python
# ราคาที่ซื้อจริงควรต่ำกว่า Intrinsic Value
Buy_Price = Intrinsic_Value × (1 - Margin_of_Safety)

# ยิ่ง uncertain ยิ่งกว้าง
if highly_uncertain:
    margin = 0.50  # 50%
elif moderately_uncertain:
    margin = 0.30  # 30%
else:
    margin = 0.15  # 15%
```

#### Scenario Analysis:
```python
# ไม่ใช้ตัวเลขเดียว แต่ใช้ range
Base_Case: Growth = 5%  → Value = 150
Bull_Case: Growth = 7%  → Value = 180
Bear_Case: Growth = 3%  → Value = 120

# ใช้ distribution แทน point estimate
Expected_Value = (0.3 × 120) + (0.5 × 150) + (0.2 × 180) = 147
```

---

## Damodaran Framework Alignment

This section maps the implementation in `reverse_dcf_model.py` to Prof. Aswath Damodaran's
published reverse DCF methodology, using a three-tier alignment framework.

**Primary reference:** Damodaran, A. Valuation lectures and datasets, NYU Stern School of
Business. https://pages.stern.nyu.edu/~adamodar/New_Home_Page/lectures.html

**Thai SET dataset reference:** See [`docs/damodaran-stern-datasets-thai-set.md`](docs/damodaran-stern-datasets-thai-set.md)
for country risk premiums, emerging-market betas, and WACC benchmarks used to parameterise
the model for Thai stocks.

### Formula-to-Damodaran mapping

| Component | Implementation | Damodaran Basis | Tier | Notes |
|---|---|---|---|---|
| Binary search solver | `low = -0.50`, `high = 1.00` | Damodaran reverse-DCF approach: solve for the growth rate that equates DCF value to market price | Tier 2 | Bounds are implementation-specific (Tier 3); the solver technique itself follows Damodaran's framing |
| High-growth phase (years 1-5) | `FCF_t = base_FCF * (1 + g)^t` | Standard DCF projection at constant growth | Tier 1 | Explicit in Damodaran's DCF lectures |
| Growth decay (years 6-10) | `g_decay = g - ((g - g_terminal) * (y-5) / 5)` | Linear interpolation from high-growth to stable-growth over a transition period | Tier 2 | Damodaran uses a declining-growth transition; linear interpolation is one common parameterisation |
| Terminal growth cap | `min(0.025, max(WACC - 0.01, 0.005))` | Damodaran recommends terminal growth <= risk-free rate and <= long-run GDP growth (~2-3%) | Tier 2 | The multi-clamp guard is Tier 3 (implementation safety) |
| Terminal value | `TV = FCF_10 * (1 + g_t) / (WACC - g_t)` | Gordon Growth Model perpetuity value | Tier 1 | Explicit in Damodaran's terminal-value treatment |
| Enterprise-to-equity bridge | `Equity = EV - Net_Debt` | Standard EV-to-equity adjustment | Tier 1 | Explicit in Damodaran |
| Signal score (backtest) | `Actual_Revenue_Growth - Implied_Growth_Rate` | Damodaran frames the investment question as: "Is the market's implied expectation above or below what the company actually delivers?" | Tier 2 | Sign convention: positive signal means realised growth exceeds market expectation |

### Tier definitions

- **Tier 1 — Explicit in Damodaran:** Formula is directly stated in lecture or textbook material.
- **Tier 2 — Derived from Damodaran principles:** Formula follows logically from his framework but
  is not given as a single explicit equation.
- **Tier 3 — Implementation-specific:** Engineering choice for Thai SET context, numerical safety,
  or code structure.

### Growth differential framing

In Damodaran's framework, the core question for a reverse DCF investor is:

> "What growth rate is the market pricing in, and does that implied growth look reasonable
> relative to what the company has actually delivered?"

The **signal score** used in the backtest captures this directly:

```
Signal_Score = Actual_Revenue_Growth - Implied_Growth_Rate
```

- **Positive score** — the company's realised growth exceeds what the market price implies;
  the market may be undervaluing future cash flows.
- **Negative score** — the market price implies growth above what the company has demonstrated;
  the stock may be overpriced relative to fundamentals.

This is consistent with Damodaran's "market expectations vs. fundamentals" lens (see
*The Little Book of Valuation*, Ch. 4, and his "Pricing vs. Valuation" lecture series).

### WACC in the backtest

For historical backtesting the pipeline uses **fixed WACC** (`--wacc-mode fixed`) to avoid
leaking current-period cost-of-capital assumptions into past rebalance dates — a form of
look-ahead bias Damodaran himself warns against when using today's ERP or beta for historical
valuation.

For current-snapshot valuation, the recommended approach uses Damodaran's Thai country risk
premium, bottom-up industry betas, and firm-specific capital structure. See
[`docs/damodaran-stern-datasets-thai-set.md`](docs/damodaran-stern-datasets-thai-set.md)
for the full dataset extraction and application rules.

### Quarterly rebalance schedule

The backtest rebalances quarterly (`rebalance_frequency = 'Q'`). This is not an arbitrary
calendar choice — it aligns with the quarterly earnings reporting cycle of Thai listed
companies. At each rebalance date:

1. Fundamental observations are selected where `Availability_Date <= Rebalance_Date`,
   ensuring only publicly available data is used.
2. Market prices are taken as of the rebalance date (or the last trading day before it).
3. New signal scores are computed from the updated fundamentals, so the portfolio naturally
   rotates when fundamentals change — not on a fixed calendar trigger.

See also the [Backtesting Guide](docs/BACKTESTING_GUIDE.md) for the no-lookahead audit
procedure that verifies this property.

---

## 📚 References

1. **Books:**
   - Damodaran, A. *The Little Book of Valuation* (Wiley, 2011)
   - Damodaran, A. *Investment Valuation* 3rd ed. (Wiley, 2012)
   - Graham, B. & Dodd, D. *Security Analysis* (McGraw-Hill)

2. **Lectures and datasets (NYU Stern):**
   - Damodaran, A. Valuation lecture series — https://pages.stern.nyu.edu/~adamodar/New_Home_Page/lectures.html
   - Country risk premiums (`ctrypremApr26.xlsx`)
   - Emerging-market betas (`betaemerg.xls`) and WACC benchmarks (`waccemerg.xls`)
   - Historical implied ERP (`histimpl.xls`) and realised premia (`histretSP.xls`)

3. **Online:**
   - Damodaran Online (NYU Stern): https://pages.stern.nyu.edu/~adamodar
   - See [`docs/damodaran-stern-datasets-thai-set.md`](docs/damodaran-stern-datasets-thai-set.md) for full dataset extraction details

---

**Bottom Line:**
> Reverse DCF เป็น **tool** ไม่ใช่ **answer**
>
> ใช้มันเพื่อ understand market expectations
> แล้วใช้ judgment ของคุณเพื่อ decide
>
> **Think with models, don't let models think for you.**
