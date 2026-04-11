# Data Directory

This directory contains all stock fundamental and price data for the Thai Stock Fundamental Data project.

## Structure

### `raw/`
Original, unprocessed data from various sources. **Do not modify files in this directory.**

- **`set100/`**: Raw data for SET100 stocks, organized by ticker
  - Each ticker folder contains original fetched data (JSON, CSV, etc.)
  - Preserves source format for provenance tracking

- **`benchmarks/`**: Benchmark indices data (e.g., SET Index)

### `processed/`
Clean, validated, and analysis-ready data.

- **`fundamentals/`**: Fundamental data matrices
  - `quarterly/`: 16 quarters of quarterly fundamental data (Parquet format)
  - `annual/`: 4+ years of annual fundamental data (Parquet format)

- **`prices/`**: Price data optimized for backtesting
  - `daily/`: Daily OHLCV data
  - `adjusted/`: Split/dividend-adjusted prices

- **`metadata/`**: Data quality and provenance information
  - `data_manifest.json`: Inventory of all data files
  - `quality_report.csv`: Data quality metrics
  - `acquisition_log.json`: Source, timestamp, and parameters for each acquisition

## Data Format

Processed data uses **Parquet** format for:
- Fast columnar access
- Efficient compression
- Schema preservation
- Pandas/Polars compatibility

## Usage

```python
import pandas as pd

# Load quarterly fundamentals
df = pd.read_parquet('data/processed/fundamentals/quarterly/fundamentals.parquet')

# Load price data
prices = pd.read_parquet('data/processed/prices/daily/prices.parquet')
```

## Data Freshness

- **Prices**: Updated daily
- **Fundamentals**: Updated quarterly after earnings releases
- Check `metadata/acquisition_log.json` for last update times
