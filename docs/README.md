# Documentation

Comprehensive documentation for the Thai Stock Fundamental Data project.

## Documents

### `DATA_ACQUISITION.md`
How to acquire data from various sources.

- Setting up data sources
- Running acquisition scripts
- Handling rate limits
- Troubleshooting acquisition issues

### `DATA_SCHEMA.md`
Data format specifications.

- Field definitions
- Data types
- Validation rules
- Examples

### `BACKTESTING_GUIDE.md`
Using the data for backtesting.

- Loading data efficiently
- Joining fundamentals and prices
- Common backtesting patterns
- Performance optimization
- Current implementation: reverse DCF ranking with benchmark-relative horizons

### `SOURCE_COMPARISON.md`
Comparison of available data sources.

- Coverage comparison
- Accuracy assessment
- Update frequency
- Cost analysis (all free methods)
- Current repository choice: Yahoo primary, SET optional validation

### `thesis-methodology.md`
Methodology chapter draft for the reverse DCF thesis workflow.

### `thesis-results.md`
Results chapter draft using the generated backtest artifacts.

## Contributing

When adding new features or data sources:

1. Update relevant documentation
2. Add examples to existing docs
3. Create new docs if needed
4. Update table of contents
5. Review for clarity and completeness

## Documentation Format

- Markdown for readability
- Code examples in Python
- Diagrams in Mermaid (where applicable)
- Version: Major.Minor.Patch
