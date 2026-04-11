import yfinance as yf
import pandas as pd
import time
from datetime import datetime

stocks_to_scrape = ['BANK.BK', 'TPI.BK']

all_data = []

for i, ticker in enumerate(stocks_to_scrape, 1):
    print(f"[{i}/{len(stocks_to_scrape)}] Scraping {ticker}...")
    
    try:
        stock = yf.Ticker(ticker)
        
        # Get quarterly income statement (last 20 quarters)
        income_stmt = stock.quarterly_income_stmt
        if income_stmt is not None and not income_stmt.empty:
            # Transpose to have dates as rows
            income_df = income_stmt.T
            
            # Get company info
            info = stock.info
            company_name = info.get('longName', ticker) if info else ticker
            
            # Add ticker and company name
            income_df.insert(0, 'Ticker', ticker)
            income_df.insert(1, 'Company_Name', company_name)
            
            all_data.append(income_df)
            print(f"  ✓ {ticker}: {len(income_df)} quarters")
        else:
            print(f"  ✗ {ticker}: No data available")
            
    except Exception as e:
        print(f"  ✗ {ticker}: Error - {str(e)}")
    
    # Small delay to be polite
    if i < len(stocks_to_scrape):
        time.sleep(2)

# Combine all data
if all_data:
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Save to CSV
    output_file = f'data/processed/stockanalysis_remaining_2_{datetime.now().strftime("%Y%m%d")}.csv'
    combined_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Saved {len(all_data)} stocks to {output_file}")
    print(f"   Total rows: {len(combined_df)}")
else:
    print("\n✗ No data collected")
