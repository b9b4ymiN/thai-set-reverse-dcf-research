#!/usr/bin/env python3
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.sources.stockanalysis_scraper import StockAnalysisScraper

def main():
    stocks = ["TID.BK", "TIP.BK", "TMB.BK", "TPI.BK"]
    output_dir = Path("/home/opc/RDCF/data/processed/metadata")
    output_dir.mkdir(parents=True, exist_ok=True)

    scraper = StockAnalysisScraper()
    scraper.min_delay = 20
    scraper.max_delay = 30

    results = {}

    for ticker in stocks:
        base_ticker = ticker.replace(".BK", "")
        print(f"\n{'='*60}")
        print(f"Scraping {ticker}...")
        print(f"{'='*60}")

        try:
            data = scraper.fetch_quarterly_financials(ticker)

            if data:
                output_path = output_dir / f"stockanalysis_{base_ticker}.json"
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"SUCCESS: Saved to {output_path}")
                results[ticker] = "SUCCESS"
            else:
                print(f"NO DATA: {ticker} returned empty data")
                results[ticker] = "NO DATA"

        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "Not Found" in error_msg:
                print(f"NOT AVAILABLE: {ticker} (404 error)")
                results[ticker] = "NOT AVAILABLE"
            else:
                print(f"ERROR: {ticker} - {error_msg}")
                results[ticker] = f"ERROR: {error_msg}"

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for ticker, status in results.items():
        print(f"{ticker}: {status}")

    return results

if __name__ == "__main__":
    main()
