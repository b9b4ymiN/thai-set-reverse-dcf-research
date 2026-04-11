import pandas as pd
from pathlib import Path
import os
import shutil
from src.pipeline.incremental_merger import IncrementalMerger

def test_yahoo_normalization():
    print("Testing Yahoo normalization...")
    merger = IncrementalMerger()
    yahoo_data = pd.DataFrame([
        {
            'Ticker': 'ADVANC.BK',
            'Period_Type': 'quarterly',
            'Statement_Date': '2023-12-31',
            'Availability_Date': '2024-02-15',
            'Reporting_Lag_Days': 45,
            'Revenue': 1000000,
            'EBIT': 200000
        }
    ])
    
    normalized = merger.normalize_source_data(yahoo_data, 'Yahoo')
    # normalized should have 2 rows (Revenue and EBIT)
    assert len(normalized) == 2
    assert 'ticker' in normalized.columns
    assert 'item_name' in normalized.columns
    assert 'value' in normalized.columns
    assert normalized[normalized['item_name'] == 'Revenue']['value'].iloc[0] == 1000000
    assert normalized[normalized['item_name'] == 'EBIT']['value'].iloc[0] == 200000
    assert (normalized['source'] == 'Yahoo').all()
    print("Yahoo normalization passed.")

def test_priority_merging():
    print("Testing priority merging...")
    test_dir = Path("data/test_tmp")
    test_dir.mkdir(parents=True, exist_ok=True)
    storage_path = test_dir / "test_fundamentals.parquet"
    if storage_path.exists():
        storage_path.unlink()
        
    merger = IncrementalMerger(storage_path=str(storage_path))
    
    # 1. Existing data from Scraped (low priority)
    scraped_data = pd.DataFrame([
        {
            'ticker': 'PTT.BK',
            'period_type': 'quarterly',
            'fiscal_date': '2023-09-30',
            'item_name': 'Revenue',
            'value': 500000,
            'source': 'Scraped'
        }
    ])
    normalized_scraped = merger.normalize_source_data(scraped_data, 'Scraped')
    merger.append_and_save(normalized_scraped)
    
    # Verify initial save
    df1 = pd.read_parquet(storage_path)
    assert len(df1) == 1
    assert df1.iloc[0]['source'] == 'Scraped'
    
    # 2. New data from Yahoo (high priority) for same record
    # PTT.BK, quarterly, 2023-09-30, Revenue
    yahoo_data = pd.DataFrame([
        {
            'Ticker': 'PTT.BK',
            'Period_Type': 'quarterly',
            'Statement_Date': '2023-09-30',
            'Availability_Date': '2023-11-15',
            'Reporting_Lag_Days': 45,
            'Revenue': 550000
        }
    ])
    normalized_yahoo = merger.normalize_source_data(yahoo_data, 'Yahoo')
    merger.append_and_save(normalized_yahoo)
    
    # Reload and verify priority
    final_df = pd.read_parquet(storage_path)
    # Ticker might be string, period_type/item_name might be category
    assert len(final_df) == 1
    assert float(final_df.iloc[0]['value']) == 550000
    assert str(final_df.iloc[0]['source']) == 'Yahoo'
    print("Priority merging passed.")

def test_new_quarter_append():
    print("Testing new quarter append...")
    test_dir = Path("data/test_tmp")
    test_dir.mkdir(parents=True, exist_ok=True)
    storage_path = test_dir / "test_fundamentals_append.parquet"
    if storage_path.exists():
        storage_path.unlink()
        
    merger = IncrementalMerger(storage_path=str(storage_path))
    
    # Initial data (Yahoo wide format)
    initial_data = pd.DataFrame([
        {
            'Ticker': 'PTT.BK',
            'Period_Type': 'quarterly',
            'Statement_Date': '2023-06-30',
            'Availability_Date': '2023-08-15',
            'Reporting_Lag_Days': 45,
            'Revenue': 400000
        }
    ])
    merger.append_and_save(merger.normalize_source_data(initial_data, 'Yahoo'))
    
    # New quarter (Yahoo wide format)
    new_data = pd.DataFrame([
        {
            'Ticker': 'PTT.BK',
            'Period_Type': 'quarterly',
            'Statement_Date': '2023-09-30',
            'Availability_Date': '2023-11-15',
            'Reporting_Lag_Days': 45,
            'Revenue': 450000
        }
    ])
    merger.append_and_save(merger.normalize_source_data(new_data, 'Yahoo'))
    
    final_df = pd.read_parquet(storage_path)
    assert len(final_df) == 2
    # Sort to be sure
    final_df = final_df.sort_values('fiscal_date')
    assert float(final_df.iloc[0]['value']) == 400000
    assert float(final_df.iloc[1]['value']) == 450000
    print("New quarter append passed.")
    
    # Cleanup
    shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_yahoo_normalization()
    test_priority_merging()
    test_new_quarter_append()
    print("All tests passed successfully!")
