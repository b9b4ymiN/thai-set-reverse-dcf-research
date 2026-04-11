import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import sys

stocks = ['BANK.BK', 'TPI.BK']

def scrape_stockanalysis(ticker):
    """Scrape data from StockAnalysis.com"""
    url = f"https://stockanalysis.com/stocks/{ticker.replace('.BK', '')}/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"  Trying {url}...")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 404:
            print(f"    ✗ 404 - Page not found")
            return None
            
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find financial data
        data = {'Ticker': ticker, 'Status': 'Found'}
        
        # Check if page has company name
        title = soup.find('h1')
        if title:
            data['Company_Name'] = title.get_text(strip=True)
            print(f"    Found: {data['Company_Name']}")
        else:
            data['Company_Name'] = ticker
            
        return data
        
    except requests.exceptions.Timeout:
        print(f"    ✗ Timeout")
        return None
    except Exception as e:
        print(f"    ✗ Error: {str(e)[:50]}")
        return None

results = []
for i, ticker in enumerate(stocks, 1):
    print(f"[{i}/{len(stocks)}] Checking {ticker}...")
    
    result = scrape_stockanalysis(ticker)
    if result:
        results.append(result)
    
    # Polite delay
    if i < len(stocks):
        time.sleep(5)

# Summary
print("\n" + "="*50)
print(f"SUMMARY: {len(results)}/{len(stocks)} stocks accessible")
print("="*50)

for r in results:
    print(f"  {r['Ticker']}: {r.get('Company_Name', 'N/A')}")

if results:
    df = pd.DataFrame(results)
    output_file = f'data/processed/stockanalysis_final_check_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    df.to_csv(output_file, index=False)
    print(f"\n✅ Saved to {output_file}")
else:
    print("\n✗ No accessible stocks found")
    print("\n💡 These stocks may be:")
    print("   - Delisted or suspended")
    print("   - Merged into other companies")
    print("   - Not covered by data sources")
