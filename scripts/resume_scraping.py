#!/usr/bin/env python3
"""
StockAnalysis.com - Resume Scraping (Batches 4-5)

Continue scraping remaining stocks after Batch 2-3 partial completion.
Will NOT abort on 404 errors (stocks not covered by StockAnalysis.com).
Only abort on rate limiting (429 errors).
"""

import sys
import time
import json
import random
from pathlib import Path
from datetime import datetime

sys.path.insert(0, 'src')

from sources.stockanalysis_scraper import StockAnalysisScraper

def get_remaining_stocks():
    """Get list of stocks that haven't been scraped yet."""

    # Load SET100 list
    set100_file = Path("research_data/set100_final/manifest.json")
    with open(set100_file) as f:
        set100_data = json.load(f)
    all_stocks = set100_data["tickers"]

    # Get already scraped stocks
    scraped = []
    metadata_dir = Path("data/processed/metadata")
    for file in metadata_dir.glob("stockanalysis_*.json"):
        if file.name != "stockanalysis_progress.json" and file.name != "stockanalysis_pilot_results.json":
            ticker = file.name.replace("stockanalysis_", "").replace(".json", "") + ".BK"
            scraped.append(ticker)

    remaining = [s for s in all_stocks if s not in scraped]
    return all_stocks, scraped, remaining

def scrape_stock(scraper, ticker):
    """Scrape a single stock, return True if successful."""

    try:
        stock_start = time.time()
        data = scraper.fetch_quarterly_financials(ticker)
        stock_time = time.time() - stock_start

        if data and "quarters" in data and len(data["quarters"]) > 0:
            num_quarters = len(set([q["quarter"] for q in data["quarters"]]))
            num_fields = len(data["quarters"])

            print(f"✅ {ticker}: {num_quarters} quarters, {num_fields} points ({stock_time:.1f}s)")

            # Save individual stock data
            stock_file = Path(f"data/processed/metadata/stockanalysis_{ticker.replace('.BK', '')}.json")
            stock_file.parent.mkdir(parents=True, exist_ok=True)
            with open(stock_file, 'w') as f:
                json.dump(data, f, indent=2)

            return True, num_fields
        else:
            print(f"❌ {ticker}: No data found")
            return False, 0

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print(f"⚠️  {ticker}: Not available on StockAnalysis.com (404)")
        else:
            print(f"❌ {ticker}: {error_msg}")

        # Only abort on rate limiting (429), continue on other errors
        if "rate" in error_msg.lower() or "429" in error_msg:
            return "RATE_LIMIT", 0
        return False, 0

def main():
    print("=" * 70)
    print("STOCKANALYSIS.COM - RESUME SCRAPING")
    print("=" * 70)
    print()

    # Get remaining stocks
    all_stocks, scraped, remaining = get_remaining_stocks()

    print(f"Total SET100: {len(all_stocks)}")
    print(f"Already scraped: {len(scraped)}")
    print(f"Remaining: {len(remaining)}")
    print()

    if len(remaining) == 0:
        print("✅ All stocks already scraped!")
        return True

    print(f"Stocks to scrape ({len(remaining)}):")
    for i, ticker in enumerate(remaining[:10], 1):
        print(f"  {i:2d}. {ticker}")
    if len(remaining) > 10:
        print(f"  ... and {len(remaining)-10} more")
    print()
    print("=" * 70)
    print()

    # Initialize scraper
    scraper = StockAnalysisScraper()
    scraper.min_delay = 30
    scraper.max_delay = 60

    results = {
        "started_at": datetime.now().isoformat(),
        "total_attempted": 0,
        "successful": 0,
        "failed": 0,
        "not_available": 0,
        "total_data_points": 0,
        "rate_limited": False,
        "aborted": False
    }

    start_time = time.time()

    # Scrape remaining stocks
    for i, ticker in enumerate(remaining, 1):
        print(f"[{i}/{len(remaining)}] {ticker}...", end=" ")

        result, data_points = scrape_stock(scraper, ticker)

        results["total_attempted"] += 1

        if result == "RATE_LIMIT":
            results["rate_limited"] = True
            results["aborted"] = True
            print("\n" + "!" * 70)
            print("RATE LIMITING DETECTED - ABORTING")
            print("!" * 70)
            break
        elif result:
            results["successful"] += 1
            results["total_data_points"] += data_points
        elif "404" in str(result) or result is False:
            results["failed"] += 1
            results["not_available"] += 1

        # Pause between stocks (except last)
        if i < len(remaining):
            pause = random.uniform(30, 60)
            print(f"  (waiting {pause:.0f}s)")
            time.sleep(pause)
        else:
            print()

    # Finalize
    results["completed_at"] = datetime.now().isoformat()
    results["total_time_seconds"] = time.time() - start_time

    # Save results
    results_file = Path("data/processed/metadata/resume_scraping_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total attempted: {results['total_attempted']}")
    print(f"✅ Successful: {results['successful']}")
    print(f"⚠️  Not available (404): {results['not_available']}")
    print(f"📊 Total data points: {results['total_data_points']}")
    print(f"⏱️  Total time: {results['total_time_seconds']/60:.1f} minutes")
    print()

    total_scraped = len(scraped) + results['successful']
    print(f"TOTAL STOCKS SCRAPED: {total_scraped}/{len(all_stocks)}")
    print("=" * 70)
    print()

    return not results["aborted"]

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
