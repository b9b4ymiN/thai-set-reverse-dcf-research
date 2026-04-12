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
  --output-dir research_data/source_of_truth_100/backtest \
  --top-n 10 \
  --horizons 3 6 12 \
  --rebalance-frequency Q \
  --start-date 2020-01-01
```

## Inputs

- `research_data/source_of_truth_100/fundamentals_snapshot.csv`
- `research_data/source_of_truth_100/fundamental_observations.csv`
- `research_data/source_of_truth_100/price_history.csv`
- `research_data/source_of_truth_100/benchmark_history.csv`

## Method

The backtest implements a reverse DCF approach following Prof. Aswath Damodaran's framework.
For methodology alignment details and formula-to-Damodaran mapping, see [`METHODOLOGY.md`](../METHODOLOGY.md).

### Quarterly rebalance when fundamentals change

Rebalancing occurs quarterly (`--rebalance-frequency Q`), timed to the earnings reporting
cycle of Thai listed companies. This is not an arbitrary calendar schedule — the portfolio
rotates when fundamentals change:

1. At each rebalance date, only observations with `Availability_Date <= Rebalance_Date`
   are eligible, so the portfolio responds to newly reported financials, not stale data.
2. Market prices are taken as of the rebalance date (or the last trading day before it).
3. Updated signal scores re-rank the universe, naturally rotating holdings when a company's
   fundamentals shift relative to its market-implied expectations.

### Signal construction

For each eligible ticker at each rebalance date:

1. Select the latest observation where `Availability_Date <= Rebalance_Date`
2. Get the last available adjusted price on or before the rebalance date
3. Solve reverse DCF using:
   - FCF from the dated observation
   - shares from diluted/issued shares
   - net debt from the dated observation
   - WACC from a **fixed backtest assumption** (`--wacc-mode fixed`, default) to avoid
     future leakage (Damodaran warns against using current-period WACC for historical
     valuations — see [`docs/damodaran-stern-datasets-thai-set.md`](damodaran-stern-datasets-thai-set.md))
4. Rank by `Signal_Score = Actual_Revenue_Growth - Implied_Growth_Rate`
   - Positive score: realised growth exceeds market-implied expectation (potential undervaluation)
   - Negative score: market expects more growth than the company has demonstrated
5. Form an equal-weight top-N portfolio
6. Compare forward return vs benchmark for each horizon

### Baseline vs risk-control cases

The pipeline supports two case families via `--case-name`:

- **Baseline** (`baseline_top5`, `baseline_top10`): Pure Damodaran-style quarterly
  rebalance with no stop-loss. This is the reference model.
- **Risk-control** (`risk_control_top5_sl5`, etc.): Quarterly rebalance plus a daily
  stop-loss overlay (5% or 10%) with a buy-ban rule. Risk controls are a separate
  overlay, not part of the Damodaran baseline.

Use `--matrix` to generate all six cases in a single run.

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
  --output-dir research_data/source_of_truth_100/backtest \
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
python -m src.pipeline.backtest_visuals --output-dir research_data/source_of_truth_100/backtest/figures
```

Figure outputs:
- `active_return_by_horizon.png`
- `hit_rate_by_horizon.png`
- `sector_active_return_heatmap.png`
- `wacc_sensitivity.png`

Package the final bundle:

```bash
python -m src.pipeline.thesis_bundle --output-dir research_data/source_of_truth_100/thesis_bundle
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
