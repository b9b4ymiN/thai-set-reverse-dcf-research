#!/usr/bin/env python3
"""
StockAnalysis.com - Batch 1 Test (Top 20 Priority Stocks)

Testing first batch with 20 stocks to validate approach before full execution.
Conservative rate limiting: 30-60 seconds between stocks.
Estimated time: ~50 minutes

Will abort if:
- Success rate drops below 80%
- Any rate limiting detected
- Takes longer than 60 minutes
"""

import sys
import time
import json
import random
from pathlib import Path
from datetime import datetime

sys.path.insert(0, 'src')

from sources.stockanalysis_scraper import StockAnalysisScraper

def run_batch_1():
    """Run batch 1 with top 20 priority stocks."""

    print("=" * 70)
    print("STOCKANALYSIS.COM - BATCH 1 TEST")
    print("=" * 70)
    print()
    print("Strategy:")
    print("  - Top 20 priority stocks")
    print("  - Conservative delays: 30-60 seconds between stocks")
    print("  - Immediate abort if rate limiting detected")
    print("  - Stop if success rate < 80%")
    print()
    print("Estimated time: ~50 minutes")
    print("Will save progress after each successful stock")
    print()
    print("=" * 70)
    print()

    # Load priority stocks
    priority_file = Path("data/processed/metadata/priority_stocks.json")
    if not priority_file.exists():
        print("ERROR: priority_stocks.json not found")
        return False

    with open(priority_file, 'r') as f:
        priority_data = json.load(f)

    # Get top 20 stocks
    batch_1_stocks = [s["ticker"] for s in priority_data["top_20_stocks"][:20]]

    print(f"Batch 1 Stocks (20 total):")
    for i, ticker in enumerate(batch_1_stocks[:10], 1):
        print(f"  {i:2d}. {ticker}")
    print("  ...")
    for i, ticker in enumerate(batch_1_stocks[10:], 11):
        print(f"  {i:2d}. {ticker}")
    print()
    print("=" * 70)
    print()

    # Initialize scraper with enhanced rate limiting
    scraper = StockAnalysisScraper()

    # Override delays for batch 1 (more conservative)
    scraper.min_delay = 30
    scraper.max_delay = 60

    results = {
        "batch_id": 1,
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

    start_time = time.time()

    # Test each stock
    for i, ticker in enumerate(batch_1_stocks, 1):
        print(f"\n[{i}/{len(batch_1_stocks)}] Testing {ticker}...")
        print("-" * 70)

        # Check success rate so far
        if len(results["successful"]) > 0:
            success_rate = len(results["successful"]) / i
            print(f"Current success rate: {success_rate:.1%}")

            if success_rate < 0.8 and i >= 5:  # At least 5 stocks tested
                print(f"\n⚠️  SUCCESS RATE BELOW 80% - ABORTING")
                results["aborted"] = True
                results["abort_reason"] = f"Success rate {success_rate:.1%} below 80% threshold"
                break

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

                    results["successful"].append(ticker)
                    results["total_data_points"] += num_fields
                    results["stocks_tested"].append({
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
                    results["failed"].append(ticker)
                    results["errors"].append(f"{ticker}: No data returned")

            else:
                print(f"❌ FAILED - Request returned None")
                results["failed"].append(ticker)
                results["errors"].append(f"{ticker}: Request failed")

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results["failed"].append(ticker)
            results["errors"].append(f"{ticker}: {str(e)}")

            # Check for rate limiting
            if "rate" in str(e).lower() or "429" in str(e):
                results["rate_limited"] = True
                print("\n" + "!" * 70)
                print("RATE LIMITING DETECTED!")
                print("Aborting batch 1.")
                print("!" * 70)
                results["aborted"] = True
                results["abort_reason"] = "Rate limiting detected"
                break

        # Check total time
        elapsed = time.time() - start_time
        if elapsed > 3600:  # 60 minutes
            print(f"\n⚠️  TAKING TOO LONG ({elapsed/60:.1f} minutes) - ABORTING")
            results["aborted"] = True
            results["abort_reason"] = f"Exceeded 60 minute limit"
            break

        # Conservative pause between stocks (except last)
        if i < len(batch_1_stocks):
            pause = random.uniform(30, 60)
            print(f"\n⏸️  Pausing for {pause:.1f} seconds before next stock...")
            time.sleep(pause)

    # Save batch results
    results["completed_at"] = datetime.now().isoformat()
    results["total_time_seconds"] = time.time() - start_time
    results_file = Path("data/processed/metadata/batch_1_results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print()
    print("=" * 70)
    print("BATCH 1 TEST SUMMARY")
    print("=" * 70)

    if results["aborted"]:
        print(f"❌ ABORTED: {results['abort_reason']}")

    print(f"Total tested: {len(results['stocks_tested'])}")
    print(f"✅ Successful: {len(results['successful'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print(f"📊 Total data points: {results['total_data_points']}")
    print(f"🚫 Rate limited: {'Yes' if results['rate_limited'] else 'No'}")
    print(f"⏱️  Total time: {results['total_time_seconds']/60:.1f} minutes")
    print()

    if results['successful']:
        success_rate = len(results['successful']) / len(batch_1_stocks)
        print(f"Success Rate: {success_rate:.1%}")
        print()

    if results['errors']:
        print("Errors:")
        for error in results['errors']:
            print(f"  - {error}")

    print()
    print("=" * 70)
    print("RECOMMENDATION:")
    print("=" * 70)

    success_rate = len(results['successful']) / len(batch_1_stocks)

    if results["aborted"]:
        if results["rate_limited"]:
            print("❌ BATCH 1 FAILED - Rate limiting detected")
            print("   → StockAnalysis.com not suitable for scraping")
            print("   → Consider alternative data sources")
        else:
            print(f"❌ BATCH 1 FAILED - {results['abort_reason']}")
            print("   → Review issues and adjust approach")
    elif success_rate >= 0.9:
        print("✅ BATCH 1 SUCCESSFUL - Excellent results!")
        print("   → Success rate ≥90% - Proceed with remaining batches")
        print("   → Continue with batches 2-5")
    elif success_rate >= 0.8:
        print("✅ BATCH 1 ACCEPTABLE - Good results")
        print("   → Success rate 80-90% - Proceed with caution")
        print("   → Monitor closely during remaining batches")
    else:
        print("⚠️  BATCH 1 MARGINAL - Below 80% success")
        print("   → Success rate <80% - Reconsider approach")
        print("   → May not be worth continuing")

    print("=" * 70)
    print(f"\nResults saved to: {results_file}")
    print()

    return success_rate >= 0.8 and not results["aborted"]

if __name__ == "__main__":
    success = run_batch_1()
    sys.exit(0 if success else 1)
