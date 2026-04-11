# Backtesting Guide

## Quick demo

```bash
python3 -m src.pipeline.demo --output-dir research_data/demo
```

This command writes a deterministic local dataset plus the backtest summary,
appendix, figures, and thesis-style bundle without fetching live data.

## Command

```bash
python -m src.pipeline.backtest \
  --output-dir research_data/latest/backtest \
  --top-n 10 \
  --horizons 3 6 12 \
  --rebalance-frequency Q \
  --start-date 2020-01-01
```

## Inputs

- `research_data/latest/fundamentals_snapshot.csv`
- `research_data/latest/fundamental_observations.csv`
- `research_data/latest/price_history.csv`
- `research_data/latest/benchmark_history.csv`

## Method

1. For each rebalance date, select the latest observation where `Availability_Date <= Rebalance_Date`
2. Get the last available adjusted price on or before the rebalance date
3. Solve reverse DCF using:
   - FCF from the dated observation
   - shares from diluted/issued shares
   - net debt from the dated observation
   - WACC from a **fixed backtest assumption** (`--wacc-mode fixed`, default) to avoid future leakage
4. Rank by `Signal_Score = Actual_Revenue_Growth - Implied_Growth_Rate`
5. Form an equal-weight top-N portfolio
6. Compare forward return vs benchmark for each horizon

## Outputs

- `signals.csv` — cross-sectional signal table per rebalance date
- `portfolio_returns.csv` — portfolio-level results per horizon
- `exclusions.csv` — excluded tickers and reasons per rebalance
- `summary.csv` — average portfolio/benchmark/active returns and hit rate
- `report.md` — thesis-friendly markdown summary
- `audit_sample.csv` — sample no-look-ahead audit rows
- `no_lookahead_audit.md` — readable markdown audit summary
- `manifest.json` — run metadata including `no_lookahead_failures`, `wacc_mode`

## Extended analysis

Generate sector and WACC-sensitivity appendices:

```bash
python -m src.pipeline.backtest_analysis \
  --output-dir research_data/latest/backtest \
  --wacc-values 0.06 0.08 0.10 \
  --top-n 10 \
  --horizons 3 6 12 \
  --rebalance-frequency Q \
  --start-date 2020-01-01
```

Additional outputs:
- `sector_summary.csv`
- `wacc_sensitivity.csv`
- `appendix.md`

Generate figures:

```bash
python -m src.pipeline.backtest_visuals --output-dir research_data/latest/backtest/figures
```

Figure outputs:
- `active_return_by_horizon.png`
- `hit_rate_by_horizon.png`
- `sector_active_return_heatmap.png`
- `wacc_sensitivity.png`

Package the final bundle:

```bash
python -m src.pipeline.thesis_bundle --output-dir research_data/latest/thesis_bundle
```

The bundle now includes:
- methodology
- results
- executive summary
- presentation script
- defense outline
- Q&A sheet
- appendix
- figures
- `analysis_manifest.json`

## Interpretation

- `Active_Return > 0` means the selected portfolio outperformed the benchmark
- `Hit_Rate` is the percentage of rebalance windows where portfolio return beat the benchmark
- `No_Lookahead_Pass` should stay `true` for all signal rows when using `--wacc-mode fixed`
