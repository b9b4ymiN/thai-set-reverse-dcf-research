from __future__ import annotations

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Union, Dict

try:
    from .acquisition import FUNDAMENTAL_ITEM_UNITS
except ImportError:
    # Fallback if circular import or other issues
    FUNDAMENTAL_ITEM_UNITS = {
        "Revenue": "THB",
        "EBIT": "THB",
        "FCF": "THB",
        "Total_Debt": "THB",
        "Total_Cash": "THB",
        "Net_Debt": "THB",
        "Shares_Issued": "shares",
        "Diluted_Average_Shares": "shares",
        "Revenue_Growth": "ratio",
    }

class IncrementalMerger:
    """
    Handles merging fundamental data from multiple sources with priority logic.
    Deduplication is performed based on (ticker, period_type, fiscal_date, item_name).
    Source priority: Yahoo > SET > Scraped
    """
    
    SOURCE_PRIORITY = {
        'Yahoo': 3,
        'SET': 2,
        'Scraped': 1
    }

    def __init__(self, storage_path: str = "data/processed/fundamentals/quarterly/fundamentals.parquet"):
        self.storage_path = Path(storage_path)
        self.standard_columns = [
            'ticker', 'period_type', 'fiscal_date', 'report_date', 
            'item_name', 'value', 'unit', 'source', 'updated_at'
        ]

    def normalize_source_data(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """
        Normalize data from a specific source to the standard long format.
        """
        if df.empty:
            return pd.DataFrame(columns=self.standard_columns)

        if source == 'Yahoo':
            return self._normalize_yahoo(df)
        elif source == 'SET':
            return self._normalize_generic(df, 'SET')
        elif source == 'Scraped':
            return self._normalize_generic(df, 'Scraped')
        else:
            # Try generic normalization if source is unknown but might follow standard
            return self._normalize_generic(df, source)

    def _normalize_yahoo(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize Yahoo Finance observations (wide format) to standard long format.
        """
        # Mapping for Yahoo columns if they differ slightly from our standard item names
        # Based on STATEMENT_OBSERVATION_FIELDS in yahoo_source.py
        metadata_cols = ['Ticker', 'Period_Type', 'Statement_Date', 'Availability_Date', 'Reporting_Lag_Days']
        item_cols = [c for c in df.columns if c not in metadata_cols]
        
        long_df = df.melt(
            id_vars=['Ticker', 'Period_Type', 'Statement_Date', 'Availability_Date'],
            value_vars=item_cols,
            var_name='item_name',
            value_name='value'
        )
        
        long_df = long_df.rename(columns={
            'Ticker': 'ticker',
            'Period_Type': 'period_type',
            'Statement_Date': 'fiscal_date',
            'Availability_Date': 'report_date'
        })
        
        long_df['source'] = 'Yahoo'
        long_df['updated_at'] = datetime.now().isoformat()
        long_df['unit'] = long_df['item_name'].map(FUNDAMENTAL_ITEM_UNITS).fillna('unknown')
        
        # Ensure fiscal_date and report_date are strings (ISO format)
        long_df['fiscal_date'] = pd.to_datetime(long_df['fiscal_date']).dt.strftime('%Y-%m-%d')
        long_df['report_date'] = pd.to_datetime(long_df['report_date']).dt.strftime('%Y-%m-%d')
        
        return long_df[self.standard_columns]

    def _normalize_generic(self, df: pd.DataFrame, source_name: str) -> pd.DataFrame:
        """
        Generic normalization for sources that might already be in long format
        or need minor adjustments.
        """
        normalized = df.copy()
        
        # Column mapping if they use PascalCase or other variants
        mapping = {
            'Ticker': 'ticker',
            'Period_Type': 'period_type',
            'Fiscal_Date': 'fiscal_date',
            'Report_Date': 'report_date',
            'Item_Name': 'item_name',
            'Value': 'value',
            'Unit': 'unit',
            'Source': 'source',
            'Updated_At': 'updated_at'
        }
        normalized = normalized.rename(columns=mapping)
        
        # Ensure all standard columns exist
        if 'source' not in normalized.columns:
            normalized['source'] = source_name
        if 'updated_at' not in normalized.columns:
            normalized['updated_at'] = datetime.now().isoformat()
        if 'unit' not in normalized.columns:
            normalized['unit'] = normalized['item_name'].map(FUNDAMENTAL_ITEM_UNITS).fillna('unknown')
            
        # If it's in wide format (has item columns but not 'item_name'), melt it
        if 'item_name' not in normalized.columns and 'value' not in normalized.columns:
            # Try to identify potential item columns from FUNDAMENTAL_ITEM_UNITS
            known_items = list(FUNDAMENTAL_ITEM_UNITS.keys())
            present_items = [c for c in normalized.columns if c in known_items]
            if present_items:
                id_vars = [c for c in normalized.columns if c not in present_items]
                normalized = normalized.melt(
                    id_vars=id_vars,
                    value_vars=present_items,
                    var_name='item_name',
                    value_name='value'
                )

        # Final cleanup
        for col in self.standard_columns:
            if col not in normalized.columns:
                normalized[col] = None
        
        # Date formatting
        if 'fiscal_date' in normalized.columns:
            normalized['fiscal_date'] = pd.to_datetime(normalized['fiscal_date']).dt.strftime('%Y-%m-%d')
        if 'report_date' in normalized.columns and normalized['report_date'].notna().any():
            normalized['report_date'] = pd.to_datetime(normalized['report_date']).dt.strftime('%Y-%m-%d')

        return normalized[self.standard_columns]

    def merge(self, new_data: pd.DataFrame) -> pd.DataFrame:
        """
        Merge new data with existing data, applying source priority and deduplication.
        Does NOT save to disk.
        """
        if new_data.empty:
            if self.storage_path.exists():
                return pd.read_parquet(self.storage_path)
            return pd.DataFrame(columns=self.standard_columns)

        existing_df = pd.DataFrame()
        if self.storage_path.exists():
            existing_df = pd.read_parquet(self.storage_path)

        combined = pd.concat([existing_df, new_data], ignore_index=True)
        
        # Apply source priority
        combined['priority'] = combined['source'].map(self.SOURCE_PRIORITY).fillna(0)
        
        # Sort by primary keys, priority (desc), and updated_at (desc)
        # Primary keys: ticker, period_type, fiscal_date, item_name
        combined = combined.sort_values(
            by=['ticker', 'period_type', 'fiscal_date', 'item_name', 'priority', 'updated_at'],
            ascending=[True, True, True, True, False, False]
        )
        
        # Drop duplicates, keeping the highest priority / newest record
        final_df = combined.drop_duplicates(
            subset=['ticker', 'period_type', 'fiscal_date', 'item_name'],
            keep='first'
        )
        
        return final_df.drop(columns=['priority'])

    def append_and_save(self, new_data: pd.DataFrame):
        """
        Normalize (if needed), merge and save to the storage path.
        """
        final_df = self.merge(new_data)
        
        # Ensure categories for optimization (consistent with FundamentalStore)
        final_df['ticker'] = final_df['ticker'].astype('string')
        final_df['period_type'] = final_df['period_type'].astype('category')
        final_df['item_name'] = final_df['item_name'].astype('category')
        
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        final_df.to_parquet(self.storage_path, index=False, compression='snappy')
        return final_df
