# Scripts

Standalone scripts for common data operations.

## Available Scripts

### `migrate_data.py`
Migrate existing data from legacy `research_data/` structure to new `data/` structure.

**Usage:**
```bash
python scripts/migrate_data.py --source research_data/set100_working --dest data/processed
```

**Features:**
- Preserves data integrity
- Creates metadata records
- Generates migration report

### `fetch_fundamentals.py`
Fetch fundamental data for specified tickers.

**Usage:**
```bash
# Fetch all SET100 stocks
python scripts/fetch_fundamentals.py --source set100 --periods 16

# Fetch specific tickers
python scripts/fetch_fundamentals.py --tickers ADVANC.BK,BBL.BK --source yahoo

# Specify data source
python scripts/fetch_fundamentals.py --source set100 --data-source set_scraper
```

**Options:**
- `--source`: Stock list (set100, set50, or custom file)
- `--tickers`: Comma-separated ticker list
- `--periods`: Number of quarters to fetch (default: 16)
- `--data-source`: Data source to use (yahoo, set_scraper, smartxl, investing)
- `--output`: Output directory (default: data/raw/set100)

### `update_prices.py`
Update price data to most recent available.

**Usage:**
```bash
# Update all stocks
python scripts/update_prices.py --source set100

# Update specific date range
python scripts/update_prices.py --tickers ADVANC.BK --start-date 2024-01-01
```

### `validate_data.py`
Run validation checks on processed data.

**Usage:**
```bash
# Validate all data
python scripts/validate_data.py

# Validate specific dataset
python scripts/validate_data.py --dataset fundamentals/quarterly

# Generate quality report
python scripts/validate_data.py --report output/quality_report.html
```

**Checks:**
- Missing values
- Data type consistency
- Date range coverage
- Cross-validation between sources
- Outlier detection

## Common Workflows

### Initial Setup
```bash
1. Migrate existing data
   python scripts/migrate_data.py

2. Fetch latest fundamentals
   python scripts/fundamentals.py --source set100 --periods 16

3. Validate data
   python scripts/validate_data.py
```

### Daily Updates
```bash
1. Update prices
   python scripts/update_prices.py --source set100

2. Validate new data
   python scripts/validate_data.py --dataset prices/daily
```

### Quarterly Updates (after earnings)
```bash
1. Fetch new quarterly data
   python scripts/fundamentals.py --source set100 --periods 4

2. Rebuild quarterly matrix
   python scripts/validate_data.py --rebuild-quarterly

3. Validate
   python scripts/validate_data.py
```

## Error Handling

All scripts log to `logs/` directory:
- `fetch_[timestamp].log`: Data fetch logs
- `migrate_[timestamp].log`: Migration logs
- `validate_[timestamp].log`: Validation logs

Check logs for detailed error information.
