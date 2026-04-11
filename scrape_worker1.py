#!/usr/bin/env python3
"""Scrape Thai SET stocks for Worker 1"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sources.stockanalysis_scraper import StockAnalysisScraper

# Stocks assigned to Worker 1
TICKERS = ["BANK.BK", "CIP.BK", "GLOW.BK", "IFEC.BK"]

def main():
    print("=" * 60)
    print("Worker 1: Scraping Thai SET stocks from StockAnalysis.com")
    print("=" * 60)

    # Initialize scraper
    scraper = StockAnalysisScraper()
    scraper.min_delay = 20
    scraper.max_delay = 30

    results = {}

    for ticker in TICKERS:
        print(f"\n{'='*60}")
        print(f"Scraping {ticker}...")
        print(f"{'='*60}")

        try:
            data = scraper.fetch_quarterly_financials(ticker)

            if data:
                # Save to file (remove .BK suffix)
                base_name = ticker.replace(".BK", "")
                output_path = Path("data/processed/metadata") / f"stockanalysis_{base_name}.json"

                # Create directory if needed
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Save data
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)

                results[ticker] = {
                    "status": "SUCCESS",
                    "file": str(output_path),
                    "records": len(data.get("financials", []))
                }
                print(f"✓ {ticker}: SAVED {len(data.get('financials', []))} records to {output_path}")
            else:
                results[ticker] = {
                    "status": "NOT AVAILABLE",
                    "reason": "No data returned"
                }
                print(f"✗ {ticker}: NOT AVAILABLE (no data)")

        except Exception as e:
            error_str = str(e)
            if "404" in error_str or "Not Found" in error_str:
                results[ticker] = {
                    "status": "NOT AVAILABLE",
                    "reason": "404 Not Found"
                }
                print(f"✗ {ticker}: NOT AVAILABLE (404)")
            else:
                results[ticker] = {
                    "status": "ERROR",
                    "error": error_str
                }
                print(f"✗ {ticker}: ERROR - {error_str}")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for ticker, result in results.items():
        print(f"{ticker}: {result['status']}")
        if result['status'] == "SUCCESS":
            print(f"  → {result['file']}")

    return results

if __name__ == "__main__":
    main()
