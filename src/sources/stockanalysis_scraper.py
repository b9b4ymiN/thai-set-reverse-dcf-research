"""
StockAnalysis.com Scraper - Conservative, Rate-Limited, Resume-Able

WARNING: This scraper may violate the website's Terms of Service.
Use at your own risk. Be respectful with request rates.

Strategy:
- Very long delays (10-30 seconds per request)
- Rate limiting: max 2-3 requests per minute
- Resume capability: saves progress after each successful fetch
- Random delays to appear more natural
- Session persistence to avoid repeated requests
"""

import time
import random
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd

class StockAnalysisScraper:
    """
    Conservative scraper for stockanalysis.com with rate limiting and resume capability.
    """

    def __init__(self, progress_file: str = "data/processed/metadata/stockanalysis_progress.json"):
        self.base_url = "https://stockanalysis.com"
        self.progress_file = Path(progress_file)
        self.progress = self._load_progress()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })

        # Rate limiting: very conservative
        self.min_delay = 10  # minimum 10 seconds
        self.max_delay = 30  # maximum 30 seconds
        self.last_request_time = 0

    def _load_progress(self) -> Dict:
        """Load progress from file if exists."""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            "started_at": datetime.now().isoformat(),
            "completed_tickers": [],
            "failed_tickers": [],
            "last_updated": None
        }

    def _save_progress(self):
        """Save progress to file."""
        self.progress["last_updated"] = datetime.now().isoformat()
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        now = time.time()
        time_since_last = now - self.last_request_time

        if time_since_last < self.min_delay:
            wait_time = self.min_delay - time_since_last
            print(f"Rate limiting: waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)

        # Add random jitter
        jitter = random.uniform(0, 10)
        time.sleep(jitter)

        self.last_request_time = time.time()

    def fetch_quarterly_financials(self, ticker: str) -> Optional[Dict]:
        """
        Fetch quarterly financials for a ticker.

        Returns None if failed, Dict with data if successful.
        """
        # Remove .BK suffix if present
        symbol = ticker.replace(".BK", "")

        url = f"{self.base_url}/quote/bkk/{symbol}/financials/?p=quarterly"

        try:
            self._rate_limit()
            print(f"Fetching {symbol} from stockanalysis.com...")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Check for rate limiting indicators
            if "rate limit" in response.text.lower() or "too many requests" in response.text.lower():
                print(f"WARNING: Rate limited for {symbol}")
                return None

            # Parse the data
            data = self._parse_financials_page(soup, symbol)

            # Update progress
            self.progress["completed_tickers"].append(ticker)
            self._save_progress()

            return data

        except Exception as e:
            print(f"Error fetching {symbol}: {str(e)}")
            self.progress["failed_tickers"].append(ticker)
            self._save_progress()
            return None

    def _parse_financials_page(self, soup: BeautifulSoup, symbol: str) -> Dict:
        """
        Parse the financials page HTML.

        Extract Revenue, EBIT, FCF, Debt, Cash data.
        """
        data = {
            "symbol": symbol,
            "fetched_at": datetime.now().isoformat(),
            "source": "stockanalysis.com",
            "url": f"{self.base_url}/quote/bkk/{symbol}/financials/?p=quarterly",
            "quarters": []
        }

        # Find the main table
        table = soup.find('table')
        if not table:
            print(f"Warning: No table found for {symbol}")
            return data

        # Get all rows
        rows = table.find_all('tr')
        if len(rows) < 2:
            print(f"Warning: Not enough data rows for {symbol}")
            return data

        # Extract headers (quarter dates)
        header_row = rows[0]
        headers = header_row.find_all('th')
        quarter_columns = []
        for header in headers[1:]:  # Skip first column (row label)
            text = header.get_text(strip=True)
            if text and 'Q' in text and any(char.isdigit() for char in text):
                quarter_columns.append(text)

        # Extract data for each quarter
        for row in rows[1:]:  # Skip header row
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue

            # Get row label (metric name)
            row_label = cells[0].get_text(strip=True)

            # Map to our standard field names
            field_name = None
            if row_label.lower() in ['revenue', 'operating revenue']:
                field_name = 'revenue'
            elif row_label.lower() in ['operating income', 'ebit']:
                field_name = 'ebit'
            elif row_label.lower() in ['net cash provided by operating activities', 'operating cash flow']:
                field_name = 'operating_cash_flow'
            elif 'cash flow' in row_label.lower() and 'operating' not in row_label.lower():
                field_name = 'free_cash_flow'

            if field_name:
                # Extract values for each quarter
                for i, cell in enumerate(cells[1:len(quarter_columns)+1]):
                    value_text = cell.get_text(strip=True)
                    if value_text and value_text != '-' and value_text != 'N/A':
                        # Clean the value (remove commas, etc.)
                        try:
                            # Convert to float, removing % signs and commas
                            value = value_text.replace(',', '').replace('%', '')
                            if value:
                                numeric_value = float(value)

                                # Get quarter from header
                                if i < len(quarter_columns):
                                    quarter = quarter_columns[i]

                                    # Add to data
                                    data["quarters"].append({
                                        "quarter": quarter,
                                        "field": field_name,
                                        "value": numeric_value,
                                        "raw_label": row_label
                                    })
                        except (ValueError, IndexError):
                            pass

        return data

    def scrape_multiple(self, tickers: List[str], max_tickers: Optional[int] = None):
        """
        Scrape multiple tickers with progress saving.

        Args:
            tickers: List of ticker symbols
            max_tickers: Optional limit for testing
        """
        if max_tickers:
            tickers = tickers[:max_tickers]

        # Skip already completed
        remaining = [t for t in tickers if t not in self.progress["completed_tickers"]]

        print(f"Starting scraping of {len(remaining)} tickers...")
        print(f"Already completed: {len(self.progress['completed_tickers'])}")

        results = []
        for i, ticker in enumerate(remaining, 1):
            print(f"\n[{i}/{len(remaining)}] Processing {ticker}...")

            data = self.fetch_quarterly_financials(ticker)
            if data:
                results.append(data)

            # Long pause between tickers
            if i < len(remaining):
                pause = random.uniform(20, 40)
                print(f"Pausing for {pause:.1f} seconds before next ticker...")
                time.sleep(pause)

        # Save final results
        output_file = Path("data/processed/metadata/stockanalysis_data.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n✅ Scraping complete!")
        print(f"Successfully scraped: {len(results)}")
        print(f"Failed: {len(self.progress['failed_tickers'])}")
        print(f"Data saved to: {output_file}")

        return results


def main():
    """
    Main function to run the scraper.
    """
    # Load priority stocks
    priority_file = Path("data/processed/metadata/priority_stocks.json")
    if not priority_file.exists():
        print("ERROR: priority_stocks.json not found. Run team analysis first.")
        return

    with open(priority_file, 'r') as f:
        priority_data = json.load(f)

    # Get top 5 stocks for pilot
    top_tickers = [s["ticker"] for s in priority_data["top_20_stocks"][:5]]

    print("=" * 60)
    print("StockAnalysis.com Scraper - PILOT MODE")
    print("=" * 60)
    print(f"Testing with {len(top_tickers)} stocks:")
    for t in top_tickers:
        print(f"  - {t}")
    print()
    print("WARNING: This will take approximately 10-15 minutes")
    print("due to conservative rate limiting.")
    print("=" * 60)
    print()

    scraper = StockAnalysisScraper()
    results = scraper.scrape_multiple(top_tickers)

    print("\n✅ Pilot complete!")
    print(f"Successfully scraped: {len(results)}/{len(top_tickers)}")
    print("\nNext steps:")
    print("1. Review the scraped data quality")
    print("2. Compare with Yahoo Finance data")
    print("3. Decide whether to proceed with full scraping")


if __name__ == "__main__":
    main()
