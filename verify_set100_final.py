#!/usr/bin/env python3
"""
Verify SET100 Final Complete - All 100 Stocks
"""
import pandas as pd
import json

print("=" * 70)
print("SET100 FINAL VERIFICATION - 100 STOCKS")
print("=" * 70)

# Expected 100 stocks
with open('set100_final_complete_100.txt', 'r') as f:
    lines = f.readlines()
expected_100 = [line.strip().strip("',") for line in lines if line.strip().startswith("'")]

print(f"\n📊 EXPECTED: {len(expected_100)} stocks")

# Check research bundle
try:
    with open('research_data/set100_final/manifest.json', 'r') as f:
        manifest = json.load(f)
    
    print(f"✅ Research bundle created")
    print(f"  Total tickers: {len(manifest['tickers'])}")
    print(f"  Price coverage: {manifest['rows']['price_coverage']}")
    print(f"  Fundamental coverage: {manifest['rows']['fundamental_coverage']}")
    
    # Check completeness
    price_coverage = pd.read_csv('research_data/set100_final/price_coverage.csv')
    complete = price_coverage[price_coverage['Has_Prices'] == True]
    
    print(f"\n✅ Stocks with price data: {len(complete)}/100")
    
    if len(complete) == 100:
        print(f"\n🎯🎯🎯 SUCCESS! ALL 100 STOCKS COMPLETE! 🎯🎯🎯")
    else:
        print(f"\n⚠️  Missing: {100 - len(complete)} stocks")
        
except Exception as e:
    print(f"\n⏳ Research bundle not ready yet: {str(e)[:50]}")
    print(f"Still creating...")

print("\n" + "=" * 70)
