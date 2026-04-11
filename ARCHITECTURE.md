# Thai Stock Fundamental Data Architecture

## Project Structure

```
RDCF/
├── data/
│   ├── raw/                      # Raw, unprocessed data from sources
│   │   ├── set100/              # Raw SET100 stock data
│   │   │   └── {ticker}/        # Individual stock raw data
│   │   │       ├── fundamentals.json
│   │   │       └── prices.csv
│   │   └── benchmarks/          # Benchmark indices
│   │       └── SET.BK.csv
│   │
│   └── processed/                # Clean, analysis-ready data
│       ├── fundamentals/         # Fundamental data matrices
│       │   ├── quarterly/       # Quarterly fundamental data (16 quarters)
│       │   │   ├── fundamentals.parquet
│       │   │   └── metadata.json
│       │   └── annual/          # Annual fundamental data
│       │       ├── fundamentals.parquet
│       │       └── metadata.json
│       ├── prices/              # Price data for backtesting
│       │   ├── daily/
│       │   │   └── prices.parquet
│       │   └── adjusted/
│       │       └── prices.parquet
│       └── metadata/            # Data provenance and quality
│           ├── data_manifest.json
│           ├── quality_report.csv
│           └── acquisition_log.json
│
├── src/
│   ├── data_sources/            # Data acquisition modules
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract base classes
│   │   ├── set_scraper.py      # SET website scraper
│   │   ├── smartxl_client.py   # SmartXL API client
│   │   ├── investing_scraper.py # Investing.com scraper
│   │   └── yahoo_source.py     # Yahoo Finance source (existing)
│   │
│   ├── processors/              # Data processing and validation
│   │   ├── __init__.py
│   │   ├── fundamental_validator.py
│   │   ├── price_adjuster.py
│   │   └── quarterly_builder.py
│   │
│   ├── storage/                 # Data storage layer
│   │   ├── __init__.py
│   │   ├── parquet_handler.py
│   │   └── schema.py
│   │
│   └── pipeline/                # Acquisition and processing pipelines
│       ├── __init__.py
│       ├── acquisition.py      # Main acquisition pipeline
│       ├── backtesting_prep.py # Prepare data for backtesting
│       └── provenance.py       # Track data lineage
│
├── config/
│   ├── sources.yaml             # Data source configurations
│   ├── schema.yaml              # Data schema definitions
│   └── pipeline_config.yaml     # Pipeline settings
│
├── scripts/                     # Standalone scripts
│   ├── migrate_data.py          # Migrate existing data
│   ├── fetch_fundamentals.py    # Fetch new fundamental data
│   ├── update_prices.py         # Update price data
│   └── validate_data.py         # Run validation checks
│
├── tests/
│   ├── test_data_sources/
│   ├── test_processors/
│   └── test_storage/
│
├── notebooks/                   # Jupyter notebooks for analysis
│   └── exploratory/
│
├── docs/
│   ├── DATA_ACQUISITION.md      # How to acquire data
│   ├── DATA_SCHEMA.md           # Data format specifications
│   ├── BACKTESTING_GUIDE.md     # Using data for backtesting
│   └── SOURCE_COMPARISON.md     # Comparison of data sources
│
└── research_data/               # Legacy data (will be migrated)
    └── set100_working/          # Current working data
```

## Design Principles

### 1. **Separation of Concerns**
- Raw data untouched in `data/raw/`
- Processed data ready for analysis in `data/processed/`
- Source code isolated in `src/`

### 2. **Multi-Project Reusability**
- Modular data sources (easy to add new sources)
- Standardized schema across projects
- Configurable pipeline
- Clear data provenance tracking

### 3. **Backtesting Optimization**
- Parquet format for fast columnar access
- Partitioned by time period
- Pre-computed common metrics
- Separate price/fundamental data for flexible joining

### 4. **Data Quality & Provenance**
- Validation at acquisition time
- Quality reports in `data/processed/metadata/`
- Acquisition logs tracking source, timestamp, and parameters
- Manifest files for data inventory

### 5. **Free Methods Only**
- SET website scraping (manual/automated)
- SmartXL trial period
- Investing.com scraping
- Yahoo Finance (existing)

## Data Schema

### Fundamentals Schema
```
ticker: str
period: str (YYYY-Q1, Q2, Q3, Q4)
fiscal_year: int
fiscal_quarter: int
revenue: float
revenue_growth: float
ebit: float
fcf: float
total_debt: float
total_cash: float
debt_to_equity: float
current_ratio: float
profit_margin: float
operating_margin: float
roe: float
roa: float
eps: float
book_value_per_share: float
source: str
fetched_at: datetime
```

### Price Schema
```
date: datetime
ticker: str
open: float
high: float
low: float
close: float
adj_close: float
volume: int
source: str
```

## Migration Strategy

1. **Phase 1:** Create new directory structure
2. **Phase 2:** Migrate existing data from `research_data/set100_working/`
3. **Phase 3:** Implement new data sources (SET, SmartXL, Investing.com)
4. **Phase 4:** Create quarterly fundamental data builder
5. **Phase 5:** Build backtesting preparation pipeline

## Next Steps (Worker 1 Deliverables)

- [x] Analyze current structure
- [x] Design new architecture
- [ ] Create directory structure
- [ ] Write folder READMEs
- [ ] Create migration script
- [ ] Document data schema
