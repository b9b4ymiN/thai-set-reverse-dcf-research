#!/bin/bash
# Complete SET100 Data Pipeline
# Run after set100_fetcher.py completes

set -e

echo "=================================="
echo "SET100 DATA PIPELINE"
echo "=================================="

echo "Step 1: Check if SET100 data exists"
if [ ! -f "set100_stock_data.csv" ]; then
    echo "❌ set100_stock_data.csv not found!"
    echo "Please run python3 set100_fetcher.py first"
    exit 1
fi

echo "✅ Found set100_stock_data.csv"
STOCK_COUNT=$(tail -n +2 set100_stock_data.csv | wc -l)
echo "📊 Total stocks: $STOCK_COUNT"

echo ""
echo "Step 2: Create research bundle"
python3 -m rdcf.data_pipeline \
    --output-dir research_data/set100 \
    --period 10y \
    --sync-root-snapshot

echo ""
echo "Step 3: Verify data completeness"
python3 fundamental_calculator.py research_data/set100

echo ""
echo "=================================="
echo "✅ SET100 PIPELINE COMPLETE"
echo "=================================="
echo "Files created:"
echo "  - research_data/set100/ (full dataset)"
echo "  - fundamental_analysis_report.csv"
echo ""
echo "Next steps:"
echo "  1. Review fundamental_analysis_report.csv"
echo "  2. Check stocks with insufficient data"
echo "  3. Run reverse_dcf_analysis.py"
