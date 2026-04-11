#!/usr/bin/env python3
"""
StockAnalysis.com - Batches 2-5 Execution

Complete remaining 80 stocks (batches 2-5) after successful Batch 1 test.
Conservative rate limiting: 30-60 seconds between stocks.
Cooldown: 2-3 minutes between batches.
Estimated time: ~1 hour

Will abort if:
- Success rate drops below 80%
- Any rate limiting detected
- Batch takes longer than 90 minutes
"""

import sys
import time
import json
import random
from pathlib import Path
from datetime import datetime

sys.path.insert(0, 'src')

from sources.stockanalysis_scraper import StockAnalysisScraper

def run_batch(scraper, batch_id, stocks, results):
    """Run a single batch of stocks."""

    print(f"\n{'='*70}")
    print(f"BATCH {batch_id}/5")
    print(f"{'='*70}")
    print(f"Stocks in batch: {len(stocks)}")
    print()

    batch_results = {
        "batch_id": batch_id,
        "started_at": datetime.now().isoformat(),
        "stocks_tested": [],
        "successful": [],
        "failed": [],
        "rate_limited": False,
        "total_data_points": 0,
        "errors": [],
        "aborted": False,
        "abort_reason": None
    }

    batch_start = time.time()

    for i, ticker in enumerate(stocks, 1):
        print(f"\n[{i}/{len(stocks)}] Testing {ticker}...")
        print("-" * 70)

        # Check success rate so far (informational only - don't abort on 404s)
        if len(batch_results["successful"]) > 0:
            success_rate = len(batch_results["successful"]) / i
            print(f"Current success rate: {success_rate:.1%}")
            # Note: 404 errors are expected for stocks not covered by StockAnalysis.com
            # Only abort on actual rate limiting, not on missing data

        try:
            stock_start = time.time()

            # Fetch data
            data = scraper.fetch_quarterly_financials(ticker)

            stock_time = time.time() - stock_start

            if data:
                # Check for rate limiting
                if "quarters" in data and len(data["quarters"]) > 0:
                    num_quarters = len(set([q["quarter"] for q in data["quarters"]]))
                    num_fields = len(data["quarters"])

                    print(f"✅ SUCCESS")
                    print(f"   Time: {stock_time:.1f} seconds")
                    print(f"   Quarters: {num_quarters}")
                    print(f"   Data points: {num_fields}")

                    batch_results["successful"].append(ticker)
                    batch_results["total_data_points"] += num_fields
                    batch_results["stocks_tested"].append({
                        "ticker": ticker,
                        "status": "success",
                        "quarters": num_quarters,
                        "data_points": num_fields,
                        "time_seconds": stock_time
                    })

                    # Save individual stock data
                    stock_file = Path(f"data/processed/metadata/stockanalysis_{ticker.replace('.BK', '')}.json")
                    stock_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(stock_file, 'w') as f:
                        json.dump(data, f, indent=2)

                else:
                    print(f"❌ FAILED - No data found")
                    batch_results["failed"].append(ticker)
                    batch_results["errors"].append(f"{ticker}: No data returned")

            else:
                print(f"❌ FAILED - Request returned None")
                batch_results["failed"].append(ticker)
                batch_results["errors"].append(f"{ticker}: Request failed")

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            batch_results["failed"].append(ticker)
            batch_results["errors"].append(f"{ticker}: {str(e)}")

            # Check for rate limiting
            if "rate" in str(e).lower() or "429" in str(e):
                batch_results["rate_limited"] = True
                print("\n" + "!" * 70)
                print("RATE LIMITING DETECTED!")
                print("Aborting all batches.")
                print("!" * 70)
                batch_results["aborted"] = True
                batch_results["abort_reason"] = "Rate limiting detected"
                break

        # Check batch time
        elapsed = time.time() - batch_start
        if elapsed > 5400:  # 90 minutes
            print(f"\n⚠️  BATCH TAKING TOO LONG ({elapsed/60:.1f} minutes) - ABORTING")
            batch_results["aborted"] = True
            batch_results["abort_reason"] = f"Exceeded 90 minute limit"
            break

        # Conservative pause between stocks (except last)
        if i < len(stocks):
            pause = random.uniform(30, 60)
            print(f"\n⏸️  Pausing for {pause:.1f} seconds before next stock...")
            time.sleep(pause)

    # Finalize batch results
    batch_results["completed_at"] = datetime.now().isoformat()
    batch_results["total_time_seconds"] = time.time() - batch_start

    # Save batch results
    batch_file = Path(f"data/processed/metadata/batch_{batch_id}_results.json")
    batch_file.parent.mkdir(parents=True, exist_ok=True)
    with open(batch_file, 'w') as f:
        json.dump(batch_results, f, indent=2)

    # Print batch summary
    print()
    print("=" * 70)
    print(f"BATCH {batch_id} SUMMARY")
    print("=" * 70)

    if batch_results["aborted"]:
        print(f"❌ ABORTED: {batch_results['abort_reason']}")

    print(f"Total tested: {len(batch_results['stocks_tested'])}")
    print(f"✅ Successful: {len(batch_results['successful'])}")
    print(f"❌ Failed: {len(batch_results['failed'])}")
    print(f"📊 Total data points: {batch_results['total_data_points']}")
    print(f"🚫 Rate limited: {'Yes' if batch_results['rate_limited'] else 'No'}")
    print(f"⏱️  Total time: {batch_results['total_time_seconds']/60:.1f} minutes")

    if batch_results['successful']:
        success_rate = len(batch_results['successful']) / len(stocks)
        print(f"Success Rate: {success_rate:.1%}")

    print("=" * 70)

    # Update overall results
    results["batches"].append(batch_results)
    results["total_stocks_tested"] += len(batch_results["stocks_tested"])
    results["total_successful"] += len(batch_results["successful"])
    results["total_failed"] += len(batch_results["failed"])
    results["total_data_points"] += batch_results["total_data_points"]

    if batch_results["rate_limited"]:
        results["rate_limited"] = True

    if batch_results["aborted"]:
        results["aborted"] = True
        results["abort_reason"] = f"Batch {batch_id}: {batch_results['abort_reason']}"

    return not batch_results["aborted"] and len(batch_results['successful']) / len(stocks) >= 0.8


def run_remaining_batches():
    """Run batches 2-5 with top 80 remaining priority stocks."""

    print("=" * 70)
    print("STOCKANALYSIS.COM - BATCHES 2-5 EXECUTION")
    print("=" * 70)
    print()
    print("Strategy:")
    print("  - Remaining 80 stocks (batches 2-5, 20 stocks each)")
    print("  - Conservative delays: 30-60 seconds between stocks")
    print("  - Cooldown: 2-3 minutes between batches")
    print("  - Immediate abort if rate limiting detected")
    print("  - Stop if batch success rate < 80%")
    print()
    print("Estimated time: ~1 hour")
    print("Will save progress after each successful stock")
    print()
    print("=" * 70)
    print()

    # Load SET100 stock list
    set100_file = Path("research_data/set100_final/manifest.json")
    if not set100_file.exists():
        print("ERROR: SET100 manifest not found at research_data/set100_final/manifest.json")
        return False

    with open(set100_file, 'r') as f:
        set100_data = json.load(f)

    all_stocks = set100_data["tickers"]

    # Get already scraped stocks from Batch 1
    batch_1_file = Path("data/processed/metadata/batch_1_results.json")
    if batch_1_file.exists():
        with open(batch_1_file, 'r') as f:
            batch_1 = json.load(f)
        batch_1_stocks = batch_1["successful"]
    else:
        print("ERROR: batch_1_results.json not found - please run Batch 1 first")
        return False

    # Get remaining stocks (excluding Batch 1)
    remaining_stocks = [s for s in all_stocks if s not in batch_1_stocks]

    print(f"Total SET100 stocks: {len(all_stocks)}")
    print(f"Already scraped (Batch 1): {len(batch_1_stocks)}")
    print(f"Remaining to scrape: {len(remaining_stocks)}")
    print()

    # Split remaining stocks into 4 batches
    batch_size = 20
    batch_2_stocks = remaining_stocks[0:batch_size]
    batch_3_stocks = remaining_stocks[batch_size:batch_size*2]
    batch_4_stocks = remaining_stocks[batch_size*2:batch_size*3]
    batch_5_stocks = remaining_stocks[batch_size*3:batch_size*4]

    batches = [
        (2, batch_2_stocks),
        (3, batch_3_stocks),
        (4, batch_4_stocks),
        (5, batch_5_stocks)
    ]

    print(f"Remaining Stocks (80 total):")
    for batch_id, stocks in batches:
        print(f"\nBatch {batch_id} (20 stocks):")
        for i, ticker in enumerate(stocks[:5], 1):
            print(f"  {i:2d}. {ticker}")
        if len(stocks) > 5:
            print(f"  ... and {len(stocks)-5} more")
    print()
    print("=" * 70)
    print()

    # Initialize results
    results = {
        "started_at": datetime.now().isoformat(),
        "batches": [],
        "total_stocks_tested": 0,
        "total_successful": 0,
        "total_failed": 0,
        "total_data_points": 0,
        "rate_limited": False,
        "aborted": False,
        "abort_reason": None
    }

    overall_start = time.time()

    # Initialize scraper with enhanced rate limiting
    scraper = StockAnalysisScraper()
    scraper.min_delay = 30
    scraper.max_delay = 60

    # Execute each batch
    for batch_id, stocks in batches:
        # Check if previous batch aborted
        if results["aborted"]:
            print(f"\n❌ PREVIOUS BATCH ABORTED - STOPPING EXECUTION")
            break

        # Run batch
        success = run_batch(scraper, batch_id, stocks, results)

        if not success:
            print(f"\n⚠️  Batch {batch_id} failed or had low success rate - Stopping")
            break

        # Cooldown between batches (except last)
        if batch_id < 5:
            cooldown = random.uniform(120, 180)  # 2-3 minutes
            print(f"\n⏸️  COOLDOWN: Resting for {cooldown/60:.1f} minutes before next batch...")
            print("⏸️  This helps avoid rate limiting")
            time.sleep(cooldown)

    # Finalize results
    results["completed_at"] = datetime.now().isoformat()
    results["total_time_seconds"] = time.time() - overall_start

    # Save overall results
    results_file = Path("data/processed/metadata/batches_2_5_results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Print final summary
    print()
    print("=" * 70)
    print("FINAL SUMMARY - BATCHES 2-5")
    print("=" * 70)

    if results["aborted"]:
        print(f"❌ ABORTED: {results['abort_reason']}")
        print()

    print(f"Total stocks tested: {results['total_stocks_tested']}")
    print(f"✅ Total successful: {results['total_successful']}")
    print(f"❌ Total failed: {results['total_failed']}")
    print(f"📊 Total data points: {results['total_data_points']}")
    print(f"🚫 Rate limited: {'Yes' if results['rate_limited'] else 'No'}")
    print(f"⏱️  Total time: {results['total_time_seconds']/60:.1f} minutes")

    if results['total_stocks_tested'] > 0:
        overall_success_rate = results['total_successful'] / results['total_stocks_tested']
        print(f"Overall Success Rate: {overall_success_rate:.1%}")

    # Add Batch 1 to get full picture
    print()
    print("-" * 70)
    print("COMBINED WITH BATCH 1:")
    print("-" * 70)

    batch_1_file = Path("data/processed/metadata/batch_1_results.json")
    if batch_1_file.exists():
        with open(batch_1_file, 'r') as f:
            batch_1 = json.load(f)

        total_stocks = len(batch_1["successful"]) + results['total_successful']
        total_data = batch_1["total_data_points"] + results['total_data_points']
        total_time = batch_1["total_time_seconds"] + results['total_time_seconds']

        print(f"Total stocks scraped: {total_stocks}/100")
        print(f"Total data points: {total_data}")
        print(f"Total time: {total_time/60:.1f} minutes")

    print("=" * 70)
    print()
    print(f"Results saved to: {results_file}")
    print()

    return not results["aborted"] and results['total_successful'] >= 64  # 80% of 80


if __name__ == "__main__":
    success = run_remaining_batches()
    sys.exit(0 if success else 1)
