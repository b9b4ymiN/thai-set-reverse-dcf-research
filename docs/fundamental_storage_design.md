# Fundamental Data Schema & Storage Design

## 1. Storage Format: Parquet
We will use **Apache Parquet** as the primary storage format for processed fundamental data.

### Rationale:
- **Efficiency**: Columnar storage allows reading only the required metrics (e.g., only 'Net Income' and 'Revenue' for CAGR calculation).
- **Type Safety**: Preserves data types (datetime, float, category) without the ambiguity of CSV.
- **Compression**: Significantly smaller footprint than CSV or HDF5.
- **Ecosystem**: Native support in `pandas`, `dask`, `polars`, and most backtesting engines.

## 2. Schema: Long Format (Normalized)
To ensure multi-project reusability and flexibility for varying financial statement items across different sectors (Banking vs. Energy vs. Retail), we adopt a **Long Format**.

| Column | Type | Description |
|---|---|---|
| `ticker` | `string` | The stock symbol (e.g., 'ADVANC.BK'). |
| `period_type` | `category` | 'annual' or 'quarterly'. |
| `fiscal_date` | `datetime64[ns]` | The end of the reporting period (e.g., 2023-12-31). |
| `report_date` | `datetime64[ns]` | The date the data was officially released (for backtesting look-ahead bias prevention). |
| `item_name` | `category` | Standardized metric name (e.g., 'revenue', 'net_income', 'total_assets'). |
| `value` | `float64` | The numeric value of the metric. |
| `unit` | `string` | 'THB' (standard for SET). |
| `source` | `string` | The origin of the data (e.g., 'yahoo', 'set_scraper', 'smartxl'). |
| `updated_at` | `datetime64[ns]` | Timestamp of when this record was processed. |

## 3. Directory Structure (Proposed)
- `data/raw/`: Original files from scrapers (CSV/JSON).
- `data/processed/fundamentals.parquet`: The unified dataset.
- `src/storage/`: Data access and conversion logic.
- `src/validation/`: Quality assurance logic.

## 4. Backtesting Optimization
For high-performance backtesting:
1. **Filtering by Report Date**: Use `report_date` to ensure the model only sees data available *at that time*.
2. **Standardization Mapping**: A mapping layer will convert source-specific names (e.g., "Sales Revenue" vs "Total Revenue") into unified `item_name` values.
3. **Pivoting**: Provide a utility function to quickly pivot the long format into a wide format (Ticker vs Date) for specific metrics.
