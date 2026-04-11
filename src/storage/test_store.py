import pandas as pd
from src.storage.fundamental_store import FundamentalStore

def test_store_functionality():
    store = FundamentalStore(data_path="data/processed/fundamentals.parquet")
    
    # Test loading raw
    df = store.load_raw()
    print(f"📊 Dataset summary:")
    print(df.info())
    print(f"\nUnique tickers: {df['ticker'].nunique()}")
    print(f"Unique items: {df['item_name'].unique()}")
    
    # Test getting history for one ticker
    ticker = 'ADVANC.BK'
    history = store.get_ticker_history(ticker, items=['revenue', 'ebit'])
    print(f"\n📈 History for {ticker}:")
    print(history.tail(5))
    
    # Test cross-sectional for a date
    date = '2023-12-31'
    cross = store.get_cross_sectional(date, items=['revenue', 'ebit'])
    print(f"\n🌍 Cross-sectional for {date}:")
    print(cross.head(10))

if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.getcwd())
    test_store_functionality()
