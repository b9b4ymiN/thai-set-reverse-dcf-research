# Thesis Methodology

## Research question

Can a **fundamental-only reverse DCF ranking strategy** select Thai stocks that outperform the Thai market benchmark over multiple holding periods?

## Data source policy

- **Primary source:** Yahoo Finance via `yfinance`
- **Validation source:** official SET pages for optional manual spot checks only
- **Cost constraint:** free data only
- **Datasource rule:** when freshness conflicts with backtest strength, prefer the source that gives stronger historical/backtest completeness

See also:
- `docs/datasource-decision.md`
- `research_data/latest/manifest.json`

## Dataset used in this repo

The current thesis workflow uses the generated research bundle under `research_data/latest/`.

Core inputs:
- `fundamentals_snapshot.csv`
- `fundamental_observations.csv`
- `price_history.csv`
- `benchmark_history.csv`
- `fundamental_coverage.csv`
- `price_coverage.csv`

## Observation dating

The backtest uses **historical statement observations** from Yahoo quarterly and annual statements.

Each observation contains:
- `Statement_Date`
- `Availability_Date`
- `Reporting_Lag_Days`

The execution rule is:

1. at each rebalance date, select the latest row where  
   `Availability_Date <= Rebalance_Date`
2. use the latest adjusted market price on or before the rebalance date

This is designed to reduce look-ahead bias.

## Reverse DCF signal construction

For each eligible ticker at each rebalance date:

1. take dated `FCF`, `Net_Debt`, and share-count inputs from the latest eligible observation
2. take market price from the dated price series
3. solve for the **implied growth rate** that makes DCF value equal market price
4. compare implied growth with observed historical revenue growth

Signal used in the current backtest:

`Signal_Score = Actual_Revenue_Growth - Implied_Growth_Rate`

Higher score means the company’s observed growth is stronger relative to what market price appears to imply.

## Backtest design

Current implementation:

- **Rebalance frequency:** quarterly
- **Portfolio construction:** equal-weight top 10 names by signal score
- **Benchmark:** `^SET.BK`
- **Holding periods tested:** 3, 6, 12 months
- **WACC mode:** `fixed`

The fixed-WACC mode is intentional for historical safety. It avoids leaking latest snapshot WACC into historical scoring.

## No-look-ahead controls

Current controls implemented in code and artifacts:

- only observations with `Availability_Date <= Rebalance_Date` are used
- only prices on or before the rebalance date are used
- backtest manifest records `wacc_mode`
- audit artifacts are written:
  - `research_data/latest/backtest/audit_sample.csv`
  - `research_data/latest/backtest/no_lookahead_audit.md`

The latest run recorded:
- `no_lookahead_failures = 0`

## Universe and exclusions

The backtest writes explicit exclusion artifacts instead of silently dropping names:

- `research_data/latest/backtest/exclusions.csv`
- `research_data/latest/backtest/summary.csv`

Main exclusion reasons in the current run:
- `invalid_fcf`
- `no_convergence`
- `no_price_on_or_before`
- `no_available_observation`
- `invalid_shares`

This makes the research more auditable and thesis-friendly.

## Limitations

1. **WACC is fixed in the backtest**
   - this is safer than using latest snapshot WACC historically
   - but it is still a simplifying assumption

2. **Yahoo coverage gaps remain**
   - some symbols may have incomplete price or statement history
   - coverage files must be reviewed alongside performance

3. **Universe is free-data constrained**
   - the strategy is evaluated on what the free source can actually provide

4. **Revenue growth is a simplified realized-growth reference**
   - it is not a full forecasting model

## Reproducibility commands

Build data:

```bash
python -m rdcf.data_pipeline --output-dir research_data/latest --period 10y --sync-root-snapshot
```

Run backtest:

```bash
python -m src.pipeline.backtest \
  --output-dir research_data/latest/backtest \
  --top-n 10 \
  --horizons 3 6 12 \
  --rebalance-frequency Q \
  --start-date 2020-01-01 \
  --wacc-mode fixed
```

## Validation checklist

- review `research_data/latest/backtest/manifest.json`
- review `research_data/latest/backtest/no_lookahead_audit.md`
- review `research_data/latest/backtest/exclusions.csv`
- compare `summary.csv` with `report.md`
