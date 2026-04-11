# Source Comparison

## Decision
Use **Yahoo Finance via `yfinance`** as the primary free acquisition path for this repository.

## Comparison
| Source | Role | Strengths | Limits | Decision |
|---|---|---|---|---|
| Yahoo / `yfinance` | Primary fetcher | Best scriptability, reusable Python flow, daily price history, quarterly + annual statement access already working in this repo | Unofficial wrapper; some fields can be missing | Chosen |
| SET website scraping | Official spot-check source | Good for manual reconciliation against exchange pages | Scraping is brittle; public pages are weaker for bulk historical backtests | Validation only |
| Investing.com scraping | Fallback check | Useful for ad hoc market-history checks | HTML scraping is brittle and fundamentals are not a clean single-source pipeline | Rejected as primary |
| SmartXL trial | Trial-only fallback | Can expose structured spreadsheet workflows during a trial | Not durable, not automation-friendly, and not reproducible as a long-running free pipeline | Rejected as primary |

## Why Yahoo Wins
- It is already integrated into the repo, so the acquisition path is testable now instead of being hypothetical.
- It best supports the project's actual priority: historical completeness for backtesting under a free-only constraint.
- It is the easiest option to reuse in adjacent projects because it runs directly from Python instead of depending on fragile HTML or trial-gated tooling.

## Provenance Policy
- Every acquisition run records the chosen primary source and the rejected alternatives in `data/processed/metadata/data_manifest.json`.
- The pipeline also appends a run-level entry to `data/processed/metadata/acquisition_log.json`.
- Official SET references remain optional validation artifacts, not a required second ingestion path.
