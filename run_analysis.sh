#!/bin/bash

# Thai SET Reverse DCF Analysis - Run Script
# This script automates the entire process

echo "================================"
echo "Thai SET Reverse DCF Analysis"
echo "================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Install dependencies
echo "Step 1: Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✓ Dependencies installed"
echo ""

# Build research bundle + sync root snapshot
echo "Step 2: Building research dataset bundle..."
python3 -m rdcf.data_pipeline --output-dir research_data/latest --period 10y --sync-root-snapshot
if [ $? -ne 0 ]; then
    echo "Error: Failed to build research dataset bundle"
    exit 1
fi
echo "✓ Research dataset bundle complete"
echo ""

# Run Reverse DCF analysis
echo "Step 3: Running Reverse DCF analysis..."
python3 reverse_dcf_model.py
if [ $? -ne 0 ]; then
    echo "Error: Failed to run Reverse DCF analysis"
    exit 1
fi
echo "✓ Reverse DCF analysis complete"
echo ""

# Summary
echo "================================"
echo "Analysis Complete!"
echo "================================"
echo ""
echo "Generated Files:"
echo "  - set_stock_data.csv (Raw stock data)"
echo "  - set_stock_data_quality.csv (Datasource quality report)"
echo "  - reverse_dcf_input_exclusions.csv (Reverse DCF input filter report)"
echo "  - set_validation_references.csv (Optional SET validation links)"
echo "  - research_data/latest/manifest.json (Research dataset bundle manifest)"
echo "  - research_data/latest/fundamental_observations.csv (Historical statement observations)"
echo "  - research_data/latest/fundamental_coverage.csv (Fundamental coverage by ticker)"
echo "  - research_data/latest/price_history.csv (Historical prices)"
echo "  - research_data/latest/price_coverage.csv (Price coverage by ticker)"
echo "  - research_data/latest/benchmark_history.csv (Benchmark prices)"
echo "  - reverse_dcf_results.csv (DCF analysis results)"
echo ""
echo "Next Steps:"
echo "  1. Review research_data/latest/manifest.json"
echo "  2. Review reverse_dcf_results.csv and coverage reports"
echo "  3. Use the bundle for backtest / thesis analysis"
echo ""
echo "================================"
