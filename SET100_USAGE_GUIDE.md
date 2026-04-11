# SET100 Dataset - Complete Usage Guide

## Quick Start

### 1. Verify Dataset
```bash
# Check dataset exists and is complete
ls -lh research_data/set100_working/

# Verify all 100 stocks
wc -l set100_working_100.txt

# Run quality check
python3 verify_set100_final.py
```

### 2. Run Complete Analysis
```bash
# Run the analysis pipeline
./analyze_set100.sh
```

This will:
- Calculate fundamental metrics for all 100 stocks
- Validate data quality
- Generate summary statistics
- Create analysis reports

---

## Data Access Examples

### Python

```python
import pandas as pd

# Load price history (10 years)
prices = pd.read_csv('research_data/set100_working/price_history.csv')
print(f"Price data: {len(prices):,} rows")
print(f"Date range: {prices['Date'].min()} to {prices['Date'].max()}")

# Load fundamental snapshot
fundamentals = pd.read_csv('research_data/set100_working/fundamentals_snapshot.csv')
print(f"\nFundamental data: {len(fundamentals)} stocks")
print(fundamentals[['Ticker', 'Current_Price', 'EPS', 'PE_Ratio']].head())

# Load fundamental observations (annual + quarterly)
observations = pd.read_csv('research_data/set100_working/fundamental_observations.csv')
print(f"\nObservations: {len(observations)} records")

# Filter annual data
annual = observations[observations['Period_Type'] == 'annual']
print(f"Annual records: {len(annual)}")

# Filter quarterly data
quarterly = observations[observations['Period_Type'] == 'quarterly']
print(f"Quarterly records: {len(quarterly)}")
```

### Bash Command Line

```bash
# View stock list
cat set100_working_100.txt

# Check price coverage
cat research_data/set100_working/price_coverage.csv | head -20

# Check fundamental coverage
cat research_data/set100_working/fundamental_coverage.csv

# View manifest
cat research_data/set100_working/manifest.json | python3 -m json.tool
```

---

## Analysis Workflows

### Workflow 1: Fundamental Analysis

```bash
# Run fundamental calculator
python3 fundamental_calculator.py research_data/set100_working

# View results
cat research_data/set100_working/fundamental_analysis_report.csv

# Filter for strong health stocks
grep "Strong" research_data/set100_working/fundamental_analysis_report.csv
```

**Output Columns:**
- Ticker: Stock symbol
- Annual_Years: Number of annual data years
- Quarterly_Periods: Number of quarterly periods
- 4Y_CAGR: 4-year compound annual growth rate
- Recent_Trend: Recent performance trend
- Overall_Health: Health assessment (Strong/Moderate/Weak)

### Workflow 2: Reverse DCF Analysis

```bash
# Run Reverse DCF (if available)
python3 reverse_dcf_analysis.py --input research_data/set100_working

# View exclusions
cat research_data/set100_working/reverse_dcf_exclusions.csv

# Check which stocks pass the filter
grep "True" research_data/set100_working/reverse_dcf_exclusions.csv
```

### Workflow 3: Sector Analysis

```python
import pandas as pd

# Load fundamentals
fundamentals = pd.read_csv('research_data/set100_working/fundamentals_snapshot.csv')

# Group by sector
sector_stats = fundamentals.groupby('Sector').agg({
    'Ticker': 'count',
    'Market_Cap': 'sum',
    'PE_Ratio': 'mean',
    'ROE': 'mean'
}).round(2)

sector_stats.columns = ['Count', 'Total_Market_Cap', 'Avg_PE', 'Avg_ROE']
print(sector_stats)
```

### Workflow 4: Performance Screening

```python
import pandas as pd

# Load data
fundamentals = pd.read_csv('research_data/set100_working/fundamentals_snapshot.csv')

# Define screening criteria
screen = fundamentals[
    (fundamentals['PE_Ratio'] > 0) &
    (fundamentals['PE_Ratio'] < 20) &
    (fundamentals['ROE'] > 0.10) &
    (fundamentals['Revenue_Growth'] > 0) &
    (fundamentals['Dividend_Yield'] > 2)
]

print(f"Stocks meeting criteria: {len(screen)}")
print(screen[['Ticker', 'Company_Name', 'PE_Ratio', 'ROE', 'Revenue_Growth']].to_string())
```

---

## Data Quality Metrics

### Completeness Check

```python
import pandas as pd
import json

# Load manifest
with open('research_data/set100_working/manifest.json', 'r') as f:
    manifest = json.load(f)

# Check completeness
total = len(manifest['tickers'])
price_coverage = manifest['rows']['price_coverage']
fundamental_coverage = manifest['rows']['fundamental_coverage']

print(f"Total Stocks: {total}")
print(f"Price Coverage: {price_coverage}/{total} ({price_coverage/total*100:.0f}%)")
print(f"Fundamental Coverage: {fundamental_coverage}/{total} ({fundamental_coverage/total*100:.0f}%)")

# Expected output:
# Total Stocks: 100
# Price Coverage: 100/100 (100%)
# Fundamental Coverage: 100/100 (100%)
```

### Data Freshness

```python
import pandas as pd

# Check latest data dates
fundamentals = pd.read_csv('research_data/set100_working/fundamentals_snapshot.csv')
prices = pd.read_csv('research_data/set100_working/price_history.csv')

print(f"Latest price date: {prices['Date'].max()}")
print(f"Latest fundamental date: {fundamentals['Fetched_Date'].max()}")
```

---

## Common Tasks

### Task 1: Find Top Performing Stocks

```python
import pandas as pd

# Load analysis report
report = pd.read_csv('research_data/set100_working/fundamental_analysis_report.csv')

# Sort by 4Y CAGR
top_performers = report.nlargest(10, '4Y_CAGR')
print("Top 10 Stocks by 4Y CAGR:")
print(top_performers[['Ticker', '4Y_CAGR', 'Recent_Trend', 'Overall_Health']])
```

### Task 2: Find Undervalued Stocks

```python
import pandas as pd

fundamentals = pd.read_csv('research_data/set100_working/fundamentals_snapshot.csv')

# Define undervalued criteria
undervalued = fundamentals[
    (fundamentals['PE_Ratio'] > 0) &
    (fundamentals['PE_Ratio'] < 15) &  # Low PE
    (fundamentals['ROE'] > 0.15) &      # High ROE
    (fundamentals['PB_Ratio'] < 2)      # Low PB
]

print(f"Undervalued stocks: {len(undervalued)}")
print(undervalued[['Ticker', 'PE_Ratio', 'ROE', 'PB_Ratio', 'Current_Price']].to_string())
```

### Task 3: Export to Excel

```python
import pandas as pd

# Load data
fundamentals = pd.read_csv('research_data/set100_working/fundamentals_snapshot.csv')

# Export to Excel
with pd.ExcelWriter('set100_analysis.xlsx') as writer:
    fundamentals.to_excel(writer, sheet_name='Fundamentals', index=False)
    
    # Add summary sheet
    summary = pd.DataFrame({
        'Metric': ['Total Stocks', 'Price Coverage', 'Fundamental Coverage'],
        'Value': [len(fundamentals), '100%', '100%']
    })
    summary.to_excel(writer, sheet_name='Summary', index=False)

print("✅ Exported to set100_analysis.xlsx")
```

---

## Troubleshooting

### Issue: Module not found

```bash
# Install required packages
pip install pandas yfinance
```

### Issue: Data not found

```bash
# Check if dataset exists
ls -lh research_data/set100_working/

# If missing, re-run the expansion
python3 set100_fetcher.py
```

### Issue: Analysis takes too long

```python
# Reduce dataset for testing
# Edit analyze_set100.sh and add --limit parameter

# Or analyze specific stocks
python3 fundamental_calculator.py research_data/set100_working --tickers ADVANC.BK,AOT.BK,BBL.BK
```

---

## Advanced Usage

### Custom Analysis

```python
import pandas as pd
import numpy as np

# Load all data
fundamentals = pd.read_csv('research_data/set100_working/fundamentals_snapshot.csv')
prices = pd.read_csv('research_data/set100_working/price_history.csv')
observations = pd.read_csv('research_data/set100_working/fundamental_observations.csv')

# Example: Calculate custom metrics
fundamentals['PE_ROE_Ratio'] = fundamentals['PE_Ratio'] / fundamentals['ROE']
fundamentals['EV_Revenue'] = fundamentals['Market_Cap'] / fundamentals['Revenue']

# Save custom metrics
fundamentals.to_csv('set100_custom_metrics.csv', index=False)
```

### Time Series Analysis

```python
import pandas as pd

prices = pd.read_csv('research_data/set100_working/price_history.csv')
prices['Date'] = pd.to_datetime(prices['Date'])

# Analyze specific stock
advanc = prices[prices['Ticker'] == 'ADVANC.BK'].copy()

# Calculate moving averages
advanc['MA50'] = advanc['Close'].rolling(window=50).mean()
advanc['MA200'] = advanc['Close'].rolling(window=200).mean()

# Plot (if matplotlib available)
import matplotlib.pyplot as plt
plt.figure(figsize=(12, 6))
plt.plot(advanc['Date'], advanc['Close'], label='Price')
plt.plot(advanc['Date'], advanc['MA50'], label='MA50')
plt.plot(advanc['Date'], advanc['MA200'], label='MA200')
plt.legend()
plt.title('ADVANC.BK Price and Moving Averages')
plt.show()
```

---

## Next Steps

1. **Review Analysis Results**
   - Check fundamental_analysis_report.csv
   - Identify strong performing stocks
   - Look for undervalued opportunities

2. **Run Reverse DCF**
   - Calculate intrinsic values
   - Compare with market prices
   - Identify undervalued stocks

3. **Portfolio Construction**
   - Select stocks based on criteria
   - Diversify across sectors
   - Optimize risk-return

4. **Regular Updates**
   - Update data quarterly
   - Re-run analysis
   - Track performance

---

## Support

### Documentation Files
- `SET100_EXPANSION_DOCUMENTATION.md` - Complete expansion process
- `SET100_FINAL_REPORT.md` - Project summary
- `SET100_MISSION_COMPLETE.txt` - Achievement summary

### Data Files
- `research_data/set100_working/` - Complete dataset
- `set100_working_100.txt` - Stock list
- `analyze_set100.sh` - Analysis pipeline

### Contact
For issues or questions, refer to the main project documentation or check the GitHub repository.

---

*Last Updated: 2026-04-11*
*Dataset Version: 1.0*
*Status: Production Ready*
