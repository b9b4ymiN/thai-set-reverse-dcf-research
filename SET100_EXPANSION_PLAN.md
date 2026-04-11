# แผนขยายจาก SET50 เป็น SET100

## 📊 สถานะปัจจุบัน

### ✅ SET50 (50 หุ้น) - พร้อมใช้งาน
- **ข้อมูลที่มี**: 45/50 หุ้น (90%)
- **ขาด 5 หุ้น**: BGRIM.BK, EA.BK, GLOBAL.BK, INTUCH.BK, KCE.BK
- **คุณภาพข้อมูล**: Annual 4-5 ปี, Quarterly 6 ไตรมาส

### 🎯 เป้าหมาย: SET100 (100 หุ้น)
- **ต้องเพิ่ม**: 50 หุ้นเพิ่มเติม
- **ความท้าทาย**: ขยายจาก Large Cap → Mid Cap
- **Data Sources**: Yahoo/yfinance (ฟรี), SET website (validation)

---

## 🚀 แผนขยาย 3 ขั้นตอน

### ขั้นตอนที่ 1: แก้ไข SET50 ให้ครบ (ทันที)
**Timeline**: 1 ชั่วโมง

#### 1.1 อัปเดตรายชื่อ SET50
```bash
# รันสคริปต์อัปเดต
python update_set50_list.py
```

#### 1.2 ดึงข้อมูล 5 หุ้นที่ขาด
```bash
# รัน fetcher ใหม่
python set_stock_fetcher.py
```

#### 1.3 สร้าง research bundle
```bash
python -m rdcf.data_pipeline --output-dir research_data/latest --period 10y
```

#### 1.4 ตรวจสอบ
```bash
python fundamental_calculator.py
```

**ผลลัพธ์**: SET50 ครบ 50 หุ้น พร้อมวิเคราะห์

---

### ขั้นตอนที่ 2: ระบุและเตรียม SET100 (1-2 วัน)
**Timeline**: 1-2 วัน

#### 2.1 หารายชื่อ SET100 ที่ถูกต้อง
```python
# แหล่งข้อมูล:
# - https://www.set.or.th/th/market/index/set100/overview
# - Yahoo Finance ^SET100.BK
# - รายงานดัชนี SET
```

#### 2.2 สร้าง `update_set100_list.py`
```python
# SET100 Index Constituents (100 หุ้น)
SET100_TICKERS = [
    # SET50 (50 หุ้น) - มีอยู่แล้ว
    'ADVANC.BK', 'AOT.BK', ... # 50 หุ้น

    # SET50 ไม่อยู่แต่อยู่ใน SET100 (50 หุ้นใหม่)
    # Mid-cap stocks
]
```

#### 2.3 ประเมินความเป็นไปได้
- ✅ **Data Coverage**: Yahoo/yfinance ครอบคลุม SET100 หรือไม่?
- ✅ **API Limits**: จัดการ rate limits ได้ไหม?
- ✅ **Processing Time**: 100 หุ้น = 2x เวลา SET50

---

### ขั้นตอนที่ 3: ดำเนินการขยายเป็น SET100 (2-3 วัน)
**Timeline**: 2-3 วัน

#### 3.1 อัปเดต set_stock_fetcher.py
```python
# เพิ่ม SET100_TICKERS
SET100_TICKERS = [
    # SET50 (50 stocks)
    ...existing_50,

    # Additional 50 stocks
    'BCH.BK', 'BCPG.BK', 'TRUE.BK', ...
]
```

#### 3.2 Fetch ข้อมูล SET100
```bash
# ใช้เวลานานกว่า (100 หุ้น)
python set_stock_fetcher.py  # ประมาณ 30-45 นาที
```

#### 3.3 สร้าง research bundle SET100
```bash
python -m rdcf.data_pipeline \
    --output-dir research_data/set100 \
    --period 10y \
    --sync-root-snapshot
```

#### 3.4 ตรวจสอบความครบถ้วน
```bash
python fundamental_calculator.py  # ตรวจ 100 หุ้น
python analyze_fundamental_gaps.py  # วิเคราะห์ช่องว่าง
```

---

## 📊 คาดการณ์ทรัพยากร

### ข้อมูลที่ต้องการ:
- **SET100**: 100 หุ้น (เพิ่ม 50 จาก SET50)
- **Fundamental observations**: ~800-1000 records (10x increase)
- **Price history**: 10 years × 100 stocks = 1M+ rows
- **Processing time**: 2-3x SET50

### ความท้าทาย:
1. **API Rate Limits**: Yahoo/yfinance มี limits
2. **Processing Time**: 100 หุ้น = ใช้เวลานาน
3. **Data Quality**: Mid-cap stocks อาจมีข้อมูลน้อยกว่า

### โซลูชัน:
1. ✅ **Batch Processing**: แบ่งเป็น 2-3 batches
2. ✅ **Incremental Updates**: อัปเดตทีละน้อย
3. ✅ **Error Handling**: Skip stocks ที่ไม่มีข้อมูล

---

## 🎯 Success Criteria

### เสร็จสมบูรณ์เมื่อ:
- ✅ มีข้อมูล fundamental ครบ 100 หุ้น
- ✅ Annual data: 4+ ปีสำหรับทุกหุ้น
- ✅ Quarterly data: 6+ ไตรมาสสำหรับทุกหุ้น
- ✅ Reverse DCF model ทำงานได้กับ 100 หุ้น
- ✅ Fundamental calculator วิเคราะห์ได้ทุกหุ้น

---

## 📝 Next Steps (ทันที)

### วันนี้:
1. ✅ แก้ไข 5 หุ้น SET50 ที่ขาด
2. ✅ ยืนยัน SET50 ครบ 50 หุ้น
3. ✅ เริ่มรวบรวมรายชื่อ SET100

### พรุ่งนี้:
1. สร้าง `update_set100_list.py`
2. ทดสอบ fetch 10 หุ้นแรกของ SET100

### สัปดาห์หน้า:
1. เริ่ม fetch ข้อมูล SET100 ทั้งหมด
2. ตรวจสอบคุณภาพข้อมูล

---

## ⚠️ คำเตือน

1. **Yahoo/yfinance limitations**: 
   - Mid-cap stocks อาจมีข้อมูลไม่ครบ
   - อาจต้องใช้ SET website ช่วย validate

2. **Processing time**:
   - 100 หุ้น = ใช้เวลา 2-3 ชั่วโมง
   - แนะนำให้ทำเป็น batches

3. **Data quality**:
   - บางหุ้นอาจไม่มี fundamental data ครบ
   - ต้องมี fallback mechanism

---

## 📞 การติดต่อ

หากต้องการความช่วยเหลือเพิ่มเติม:
- ตรวจสอบ `QUICKSTART.md` สำหรับการใช้งาน
- ดู `METHODOLOGY.md` สำหรับหลักการวิเคราะห์
- ใช้ `fundamental_calculator.py` ตรวจสอบความสมบูรณ์

---

**สถานะเอกสาร**: ✅ พร้อมใช้งาน
**วันที่สร้าง**: 11 เมษายน 2026
**ผู้สร้าง**: Gemini Worker-2 (verified by Claude)
