import pandas as pd
from pathlib import Path
from typing import List, Optional, Union
import pyarrow.parquet as pq

class FundamentalStore:
    """
    Standardized interface for accessing fundamental data across multiple projects.
    Handles reading from Parquet, filtering, and conversion to useful formats.
    """

    def __init__(self, data_path: str = "data/processed/fundamentals.parquet"):
        self.data_path = Path(data_path)

    def load_raw(self) -> pd.DataFrame:
        """Load the entire dataset from Parquet."""
        if not self.data_path.exists():
            return pd.DataFrame()
        return pd.read_parquet(self.data_path)

    def get_ticker_history(self, ticker: str, 
                           items: Optional[List[str]] = None,
                           period_type: str = 'quarterly') -> pd.DataFrame:
        """
        Get historical fundamentals for a single ticker in a wide format.
        """
        df = self.load_raw()
        if df.empty:
            return df
            
        ticker_df = df[(df['ticker'] == ticker) & (df['period_type'] == period_type)]
        
        if items:
            ticker_df = ticker_df[ticker_df['item_name'].isin(items)]
            
        # Pivot to wide format for easier analysis
        wide_df = ticker_df.pivot_table(
            index='fiscal_date', 
            columns='item_name', 
            values='value'
        ).sort_index()
        
        return wide_df

    def get_cross_sectional(self, date: Union[str, pd.Timestamp], 
                             items: List[str],
                             period_type: str = 'quarterly') -> pd.DataFrame:
        """
        Get fundamentals for all tickers at a specific date.
        """
        df = self.load_raw()
        if df.empty:
            return df
            
        # Note: In real scenarios, we should find the most recent record *before* or *at* the date
        # using report_date to avoid look-ahead bias.
        target_date = pd.to_datetime(date)
        
        cross_df = df[
            (df['fiscal_date'] <= target_date) & 
            (df['period_type'] == period_type) &
            (df['item_name'].isin(items))
        ]
        
        # Get the latest report for each ticker/item
        cross_df = cross_df.sort_values('fiscal_date').groupby(['ticker', 'item_name']).tail(1)
        
        wide_df = cross_df.pivot_table(
            index='ticker', 
            columns='item_name', 
            values='value'
        )
        
        return wide_df

    def save_processed(self, df: pd.DataFrame):
        """
        Save the standardized long-format DataFrame to Parquet.
        """
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        # Ensure categories for optimization
        df['ticker'] = df['ticker'].astype('string')
        df['period_type'] = df['period_type'].astype('category')
        df['item_name'] = df['item_name'].astype('category')
        
        df.to_parquet(self.data_path, index=False, compression='snappy')

    def append_new_data(self, new_df: pd.DataFrame):
        """
        Append new records to the existing Parquet store, ensuring no duplicates.
        """
        if not self.data_path.exists():
            self.save_processed(new_df)
            return

        existing_df = self.load_raw()
        # Simple deduplication based on ticker, date, item_name, period_type
        combined = pd.concat([existing_df, new_df]).drop_duplicates(
            subset=['ticker', 'fiscal_date', 'item_name', 'period_type'],
            keep='last'
        )
        self.save_processed(combined)
