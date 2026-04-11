#!/usr/bin/env python3
import sys
import json
from pathlib import Path

sys.path.insert(0, '/home/opc/RDCF')
from src.sources.stockanalysis_scraper import StockAnalysisScraper

# My assigned stocks
stocks = ['LHB.BK', 'MAK.BK', 'PLAN.BK', 'TFF.BK']

# Initialize scraper with delays
scraper = StockAnalysisScraper()
scraper.min_delay = 20
scraper.max_delay = 30

results = {}

for ticker in stocks:
    print(f"\n{'='*60}")
    print(f"Scraping {ticker}...")
    print(f"{'='*60}")

    try:
        data = scraper.fetch_quarterly_financials(ticker)

        if data is None:
            results[ticker] = 'NOT AVAILABLE'
            print(f"❌ {ticker}: NOT AVAILABLE (404 or no data)")
        else:
            # Save to file (remove .BK suffix)
            base_name = ticker.replace('.BK', '')
            output_path = Path(f'/home/opc/RDCF/data/processed/metadata/stockanalysis_{base_name}.json')
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)

            results[ticker] = 'SUCCESS'
            print(f"✅ {ticker}: SUCCESS - Saved to {output_path}")
            print(f"   Data points: {len(data.get('quarterly_financials', []))}")

    except Exception as e:
        results[ticker] = f'ERROR: {str(e)}'
        print(f"❌ {ticker}: ERROR - {e}")

print(f"\n\n{'='*60}")
print("WORKER 2 SUMMARY")
print(f"{'='*60}")
for ticker, result in results.items():
    print(f"{ticker}: {result}")
