#!/bin/bash
# SET100 Analysis Scripts - Complete Analysis Pipeline

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           SET100 ANALYSIS PIPELINE - COMPLETE ANALYSIS          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if dataset exists
if [ ! -d "research_data/set100_working" ]; then
    echo "❌ Error: research_data/set100_working not found!"
    echo "Please run the SET100 expansion first."
    exit 1
fi

echo "📊 SET100 Dataset Found"
echo ""

# Step 1: Fundamental Analysis
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Fundamental Analysis"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 fundamental_calculator.py research_data/set100_working

if [ $? -eq 0 ]; then
    echo "✅ Fundamental analysis complete"
else
    echo "❌ Fundamental analysis failed"
    exit 1
fi

echo ""

# Step 2: Data Quality Validation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Data Quality Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'PYEOF'
import pandas as pd
import json

# Read manifest
with open('research_data/set100_working/manifest.json', 'r') as f:
    manifest = json.load(f)

print(f"Total stocks: {len(manifest['tickers'])}")
print(f"Price coverage: {manifest['rows']['price_coverage']}/100")
print(f"Fundamental coverage: {manifest['rows']['fundamental_coverage']}/100")

# Check quality
price_coverage = pd.read_csv('research_data/set100_working/price_coverage.csv')
complete = len(price_coverage[price_coverage['Has_Prices'] == True])

print(f"\n✅ Data Quality: {complete}/100 stocks complete")

if complete == 100:
    print("🎯 All stocks have complete data!")
PYEOF

echo ""

# Step 3: Summary Statistics
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Summary Statistics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'PYEOF'
import pandas as pd

# Load data
prices = pd.read_csv('research_data/set100_working/price_history.csv')
fundamentals = pd.read_csv('research_data/set100_working/fundamentals_snapshot.csv')

print(f"Price history: {len(prices):,} rows")
print(f"Fundamental snapshot: {len(fundamentals)} stocks")
print(f"Date range: {prices['Date'].min()} to {prices['Date'].max()}")

# Show sample
print(f"\nSample stocks:")
print(fundamentals[['Ticker', 'Current_Price', 'EPS', 'PE_Ratio']].head(10).to_string())
PYEOF

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              ✅ ANALYSIS PIPELINE COMPLETE! ✅                  ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Results saved to:"
echo "  - research_data/set100_working/fundamental_analysis_report.csv"
echo "  - research_data/set100_working/fundamental_observations.csv"
echo ""
echo "🚀 Next steps:"
echo "  1. Review fundamental_analysis_report.csv"
echo "  2. Run reverse DCF analysis"
echo "  3. Generate portfolio insights"
