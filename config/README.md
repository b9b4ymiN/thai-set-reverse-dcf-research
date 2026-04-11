# Configuration

Configuration files for data sources, schemas, and pipelines.

## Files

### `sources.yaml`
Data source configurations including API endpoints, rate limits, and authentication.

**Structure:**
```yaml
sources:
  yahoo_finance:
    enabled: true
    rate_limit: 1000/hour
    data_types: [prices, fundamentals]

  set_scraper:
    enabled: true
    rate_limit: 60/hour
    base_url: "https://www.set.or.th"
    data_types: [fundamentals]

  smartxl:
    enabled: false  # Requires API key
    trial_period_ends: "2024-12-31"
    data_types: [fundamentals]

  investing_com:
    enabled: true
    rate_limit: 120/hour
    data_types: [prices, fundamentals]
```

### `schema.yaml`
Data schema definitions for validation and storage.

**Defines:**
- Field types and constraints
- Required vs optional fields
- Validation rules
- Index definitions

### `pipeline_config.yaml`
Pipeline execution settings.

**Settings:**
- Default data sources by priority
- Parallel processing limits
- Retry logic
- Output formats
- Quality thresholds

## Usage

```python
from ruamel.yaml import YAML

yaml = YAML()
with open('config/sources.yaml') as f:
    config = yaml.load(f)

# Get enabled sources
enabled_sources = [s for s, cfg in config['sources'].items() if cfg['enabled']]
```

## Modifying Configuration

1. Always backup before editing
2. Validate YAML syntax: `yamllint config/*.yaml`
3. Test changes with `--dry-run` flag
4. Document changes in git commit
