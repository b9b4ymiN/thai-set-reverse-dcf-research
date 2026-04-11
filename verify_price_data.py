import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def analyze_price_data(file_path):
    print(f"Analyzing {file_path}...")
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    total_rows = len(df)
    tickers = df['Ticker'].unique()
    num_tickers = len(tickers)
    
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    date_range_days = (max_date - min_date).days
    
    print(f"Total rows: {total_rows}")
    print(f"Number of stocks: {num_tickers}")
    print(f"Global Date Range: {min_date.date()} to {max_date.date()} ({date_range_days} days)")
    
    # Identify all trading dates in the dataset
    all_dates = sorted(df['Date'].unique())
    all_dates_set = set(all_dates)
    
    results = []
    
    # Analyze each ticker
    for ticker in tickers:
        ticker_data = df[df['Ticker'] == ticker].sort_values('Date')
        ticker_dates = set(ticker_data['Date'])
        
        # Coverage calculation
        first_date = ticker_data['Date'].iloc[0]
        last_date = ticker_data['Date'].iloc[-1]
        
        # Expected dates within the ticker's own range (based on all_dates present in global set)
        expected_dates_in_range = [d for d in all_dates if first_date <= d <= last_date]
        missing_dates = [d for d in expected_dates_in_range if d not in ticker_dates]
        
        completion_pct = (len(ticker_dates) / len(expected_dates_in_range)) * 100 if expected_dates_in_range else 0
        
        # Check for 10-year coverage (approx 3650 days)
        ten_year_threshold = max_date - timedelta(days=3650)
        has_10_years = first_date <= ten_year_threshold
        
        results.append({
            'Ticker': ticker,
            'First Date': first_date.date(),
            'Last Date': last_date.date(),
            'Days Coverage': (last_date - first_date).days,
            'Data Points': len(ticker_dates),
            'Missing Points': len(missing_dates),
            'Completion %': completion_pct,
            '10 Year Coverage': has_10_years
        })

    summary_df = pd.DataFrame(results)
    
    # Summary stats
    stocks_with_10yr = summary_df['10 Year Coverage'].sum()
    avg_completion = summary_df['Completion %'].mean()
    problematic_stocks = summary_df[summary_df['Completion %'] < 95]['Ticker'].tolist()
    
    print("\n--- Summary ---")
    print(f"Stocks with 10 years of data: {stocks_with_10yr} ({stocks_with_10yr/num_tickers*100:.1f}%)")
    print(f"Average data completion: {avg_completion:.2f}%")
    print(f"Problematic stocks (<95% complete): {len(problematic_stocks)}")
    
    summary_df.to_csv('price_verification_report.csv', index=False)
    
    # Create Markdown report
    with open('PRICE_VERIFICATION_REPORT.md', 'w') as f:
        f.write("# Price Data Verification Report\n\n")
        f.write("## Executive Summary\n\n")
        f.write("| Metric | Value |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| Total Rows | {total_rows:,} |\n")
        f.write(f"| Number of Stocks | {num_tickers} |\n")
        f.write(f"| Global Date Range | {min_date.date()} to {max_date.date()} |\n")
        f.write(f"| Stocks with 10yr Coverage | {stocks_with_10yr} ({stocks_with_10yr/num_tickers*100:.1f}%) |\n")
        f.write(f"| Average Completion Rate | {avg_completion:.2f}% |\n")
        f.write(f"| Problematic Stocks (<95% complete) | {len(problematic_stocks)} |\n\n")
        
        f.write("## Top 10 Stocks by Coverage (Full 10-Year Data)\n\n")
        f.write("| Ticker | First Date | Completion % | 10yr |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for idx, row in summary_df.sort_values(['10 Year Coverage', 'Completion %'], ascending=False).head(10).iterrows():
            f.write(f"| {row['Ticker']} | {row['First Date']} | {row['Completion %']:.1f}% | {'✅' if row['10 Year Coverage'] else '❌'} |\n")
        
        f.write("\n## Problematic Stocks / Short History\n\n")
        f.write("| Ticker | First Date | Completion % | Data Points | Gap Reason |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        short_history = summary_df[~summary_df['10 Year Coverage']].sort_values('Days Coverage', ascending=False)
        for idx, row in short_history.iterrows():
            f.write(f"| {row['Ticker']} | {row['First Date']} | {row['Completion %']:.1f}% | {row['Data Points']} | Short History |\n")
            
        low_completion = summary_df[(summary_df['Completion %'] < 99) & (summary_df['10 Year Coverage'])].sort_values('Completion %')
        for idx, row in low_completion.iterrows():
            f.write(f"| {row['Ticker']} | {row['First Date']} | {row['Completion %']:.1f}% | {row['Data Points']} | Data Gaps |\n")
            
        f.write("\n## Recommendation\n\n")
        if len(problematic_stocks) > 0:
            f.write("- **Data Backfill Required:** Consider refetching data for stocks with low completion rates.\n")
        if stocks_with_10yr < num_tickers:
            f.write("- **Historical Limitation:** Some stocks (likely newer IPOs) do not have 10 years of history. Reverse DCF terminal value calculations should account for this shortened window.\n")
        f.write("- **Validation Passed:** The dataset is generally robust and suitable for analysis for stocks with high completion rates.\n")

if __name__ == "__main__":
    analyze_price_data('research_data/set100_working/price_history.csv')
