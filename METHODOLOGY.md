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

## 📚 References

1. **Books:**
   - "The Little Book of Valuation" - Aswath Damodaran
   - "Security Analysis" - Benjamin Graham

2. **Academic Papers:**
   - Damodaran, A. (2012). "Investment Valuation"
   - Koller, T. (2015). "Valuation"

3. **Online:**
   - Damodaran Online (NYU Stern)
   - Investopedia DCF articles

---

**Bottom Line:**
> Reverse DCF เป็น **tool** ไม่ใช่ **answer**
>
> ใช้มันเพื่อ understand market expectations
> แล้วใช้ judgment ของคุณเพื่อ decide
>
> **Think with models, don't let models think for you.**
