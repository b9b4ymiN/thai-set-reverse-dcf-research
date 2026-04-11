# Datasource Decision

## Decision
Use **Yahoo Finance via `yfinance`** as the primary free datasource for this repository's reverse-DCF workflows.

## Why
- It is already integrated into the project.
- It is free and script-friendly.
- It offers a more practical path for historical backtest completeness than the free public SET website.
- The datasource adapter can be reused in other Thai-equity projects.

## Rejected alternatives
### Free official SET website as primary source
Rejected as the thesis-core datasource because its free public web experience appears too shallow for long-horizon backtests compared with the paid SETSMART offering.

### SETSMART as primary source
Rejected because it is paid and violates the project's free-only requirement.

## Validation policy
Official SET pages may still be used for optional manual spot checks, but they are **not** the default ingestion path.

## Caveat
Yahoo/`yfinance` is practical, not perfect. The project must log field coverage, exclusions, and datasource limitations explicitly in research outputs.
