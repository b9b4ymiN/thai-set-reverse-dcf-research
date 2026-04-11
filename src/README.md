# Source Code

This directory contains all Python source code for data acquisition, processing, and storage.

## Modules

### `pipeline/`
Workflow modules for acquisition and backtesting.

- **`acquisition.py`**: main acquisition pipeline with provenance manifests
- **`backtest.py`**: reverse DCF backtest engine and CLI
- **`provenance.py`**: source review, quality summaries, and acquisition metadata

### `storage/`
Data access helpers.

- **`fundamental_store.py`**: read/write standardized long-format fundamentals
- **`migrate_v1_to_v2.py`**: migrate legacy CSV observations to the store format

### `validation/`
Validation utilities.

- **`fundamental_validator.py`**: completeness, outlier, and accounting checks

### `pipeline/`
Orchestration and workflow management.

- **`acquisition.py`**: Main data acquisition pipeline
- **`backtest.py`**: Reverse DCF backtest engine and CLI
- **`provenance.py`**: Track data lineage and metadata

## Testing

```bash
# Run all tests
python -m unittest discover -s tests -v

# Run the backtest pipeline test only
python -m unittest tests.test_backtest_pipeline -v
```
