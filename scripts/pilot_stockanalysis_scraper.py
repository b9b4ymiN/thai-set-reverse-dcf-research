#!/usr/bin/env python3
"""
StockAnalysis.com Pilot Test - Conservative Mode

Tests scraping 5 stocks with very conservative rate limiting.
Monitors for rate limiting and aborts if any issues detected.

Runtime: ~2-3 minutes per stock = ~10-15 minutes total
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from sources.stockanalysis_scraper import StockAnalysisScraper

def check_rate_limit_indicators(response_text: str) -> bool:
    """Check if response contains rate limiting indicators."""
    indicators = [
        "rate limit",
        "too many requests",
        "429",
        "blocked",
        "access denied",
        "temporarily blocked",
        "try again later"
    ]

    text_lower = response_text.lower()
    for indicator in indicators:
        if indicator in text_lower:
            return True
    return False

def run_pilot():
    """
    Run pilot test with 5 stocks.
    """
    print("=" * 70)
    print("StockAnalysis.com PILOT TEST")
    print("=" * 70)
    print()
    print("Strategy:")
    print("  - Testing 5 stocks (Top priority)")
    print("  - Conservative delays: 20-40 seconds between stocks")
    print("  - Immediate abort if rate limiting detected")
    print("  - Save progress after each successful fetch")
    print()
    print("Estimated time: 10-15 minutes")
    print()

    # Load priority stocks
    priority_file = Path("data/processed/metadata/priority_stocks.json")
    if not priority_file.exists():
        print("ERROR: priority_stocks.json not found")
        return False

    with open(priority_file, 'r') as f:
        priority_data = json.load(f)

    # Get top 5 stocks
    pilot_stocks = [s["ticker"] for s in priority_data["top_20_stocks"][:5]]

    print(f"Pilot stocks: {', '.join(pilot_stocks)}")
    print()
    print("=" * 70)
    print()

    # Initialize scraper
    scraper = StockAnalysisScraper()

    results = {
        "started_at": datetime.now().isoformat(),
        "stocks_tested": [],
        "successful": [],
        "failed": [],
        "rate_limited": False,
        "total_data_points": 0,
        "errors": []
    }

    # Test each stock
    for i, ticker in enumerate(pilot_stocks, 1):
        print(f"\n[{i}/{len(pilot_stocks)}] Testing {ticker}...")
        print("-" * 70)

        try:
            start_time = time.time()

            # Fetch data
            data = scraper.fetch_quarterly_financials(ticker)

            elapsed = time.time() - start_time

            if data:
                # Check for rate limiting
                if "quarters" in data and len(data["quarters"]) > 0:
                    num_quarters = len(set([q["quarter"] for q in data["quarters"]]))
                    num_fields = len(data["quarters"])

                    print(f"✅ SUCCESS")
                    print(f"   Time: {elapsed:.1f} seconds")
                    print(f"   Quarters: {num_quarters}")
                    print(f"   Data points: {num_fields}")

                    results["successful"].append(ticker)
                    results["total_data_points"] += num_fields
                    results["stocks_tested"].append({
                        "ticker": ticker,
                        "status": "success",
                        "quarters": num_quarters,
                        "data_points": num_fields,
                        "time_seconds": elapsed
                    })

                    # Save individual stock data
                    stock_file = Path(f"data/processed/metadata/stockanalysis_{ticker.replace('.BK', '')}.json")
                    stock_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(stock_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"   Saved: {stock_file}")

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

            # Check if it's a rate limit error
            if "rate" in str(e).lower() or "429" in str(e):
                results["rate_limited"] = True
                print("\n" + "!" * 70)
                print("RATE LIMITING DETECTED!")
                print("Aborting pilot to avoid being blocked.")
                print("!" * 70)
                break

        # Long pause between stocks (except last one)
        if i < len(pilot_stocks):
            pause = random.uniform(20, 40)
            print(f"\n⏸️  Pausing for {pause:.1f} seconds before next stock...")
            time.sleep(pause)

    # Save pilot results
    results["completed_at"] = datetime.now().isoformat()
    results_file = Path("data/processed/metadata/stockanalysis_pilot_results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print()
    print("=" * 70)
    print("PILOT TEST SUMMARY")
    print("=" * 70)
    print(f"Total tested: {len(pilot_stocks)}")
    print(f"✅ Successful: {len(results['successful'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print(f"📊 Total data points: {results['total_data_points']}")
    print(f"🚫 Rate limited: {'Yes' if results['rate_limited'] else 'No'}")
    print()

    if results['errors']:
        print("Errors encountered:")
        for error in results['errors']:
            print(f"  - {error}")

    print()
    print(f"Results saved to: {results_file}")
    print()

    # Recommendation
    if len(results['successful']) >= 4:  # 80% success rate
        print("✅ RECOMMENDATION: Pilot successful!")
        print("   - High success rate (>80%)")
        print("   - Proceed with full scraping cautiously")
        print("   - Monitor for rate limiting throughout")
    elif len(results['successful']) >= 2:  # 40% success rate
        print("⚠️  RECOMMENDATION: Mixed results")
        print("   - Moderate success rate (40-80%)")
        print("   - Consider alternative approaches")
        print("   - May work for priority stocks only")
    else:
        print("❌ RECOMMENDATION: Pilot failed")
        print("   - Low success rate (<40%)")
        print("   - StockAnalysis.com not viable for scraping")
        print("   - Consider alternative data sources")

    print("=" * 70)

    return len(results['successful']) >= 2

if __name__ == "__main__":
    import random  # Add this for the random delay
    success = run_pilot()
    sys.exit(0 if success else 1)
