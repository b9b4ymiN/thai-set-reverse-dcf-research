import pandas as pd
from pathlib import Path
from src.storage.fundamental_store import FundamentalStore
from datetime import datetime

def migrate_existing_data():
    """Migrate from old CSV format to new standardized Parquet long format."""
    
    input_path = Path("research_data/latest/fundamental_observations.csv")
    if not input_path.exists():
        print(f"Error: {input_path} not found.")
        return

    print(f"Migrating {input_path}...")
    df = pd.read_csv(input_path)
    
    # Columns to transform from wide to long
    # Ticker,Period_Type,Statement_Date,Availability_Date,Reporting_Lag_Days,
    # Revenue,EBIT,FCF,Total_Debt,Total_Cash,Net_Debt,Shares_Issued,
    # Diluted_Average_Shares,Revenue_Growth
    
    id_vars = ['Ticker', 'Period_Type', 'Statement_Date', 'Availability_Date']
    value_vars = ['Revenue', 'EBIT', 'FCF', 'Total_Debt', 'Total_Cash', 
                  'Net_Debt', 'Shares_Issued', 'Diluted_Average_Shares']
    
    # Melt to long format
    long_df = pd.melt(
        df,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='item_name',
        value_name='value'
    )
    
    # Standardize column names
    long_df = long_df.rename(columns={
        'Ticker': 'ticker',
        'Period_Type': 'period_type',
        'Statement_Date': 'fiscal_date',
        'Availability_Date': 'report_date'
    })
    
    # Convert to datetime
    long_df['fiscal_date'] = pd.to_datetime(long_df['fiscal_date'])
    long_df['report_date'] = pd.to_datetime(long_df['report_date'])
    
    # Add extra metadata
    long_df['unit'] = 'THB'
    long_df['source'] = 'yahoo_legacy'
    long_df['updated_at'] = pd.Timestamp.now()
    
    # Clean up item names to lowercase
    long_df['item_name'] = long_df['item_name'].str.lower()
    
    # Save using the new store
    store = FundamentalStore(data_path="data/processed/fundamentals.parquet")
    store.save_processed(long_df)
    
    print(f"Migration complete! Processed {len(long_df)} records.")
    print(f"Saved to: {store.data_path}")

if __name__ == "__main__":
    migrate_existing_data()
