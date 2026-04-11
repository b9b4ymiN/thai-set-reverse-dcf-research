# Thesis Results

## Scope of this result set

This document summarizes the current backtest outputs generated from:

- `research_data/latest/backtest/summary.csv`
- `research_data/latest/backtest/report.md`
- `research_data/latest/backtest/manifest.json`
- `research_data/latest/backtest/exclusions.csv`

## Sample window

Current rebalance dates in the generated result set:

- **First rebalance:** 2023-03-31
- **Last rebalance:** 2026-03-31

## Backtest configuration

- **Strategy:** reverse DCF ranking
- **Selection rule:** top 10 by `Signal_Score`
- **Benchmark:** `^SET.BK`
- **Rebalance frequency:** quarterly
- **Horizons tested:** 3, 6, 12 months
- **WACC mode:** fixed

## Main results

### Average benchmark-relative performance

| Horizon | Portfolio Return | Benchmark Return | Active Return | Hit Rate |
|---|---:|---:|---:|---:|
| 3 months | 1.6785% | -0.0034% | 1.6818% | 53.85% |
| 6 months | 2.2032% | 0.5519% | 1.6514% | 69.23% |
| 12 months | 2.4290% | 1.5788% | 0.8502% | 61.54% |

## Interpretation

### Positive findings

1. The current implementation shows **positive active return in all tested horizons**
2. The **3-month horizon** produced the highest average active return
3. The **6-month horizon** produced the highest hit rate
4. The no-look-ahead audit reported **0 failures**

### Important caution

These results do **not** mean reverse DCF is universally proven. They mean:

- under the current free-data workflow,
- with the current top-10 equal-weight design,
- with fixed-WACC historical scoring,
- the tested portfolio beat the benchmark **on average** in this sample

This should be reported as **evidence from the current design**, not as an absolute claim.

## Coverage and exclusions

Current backtest manifest:

- signals generated: **408**
- portfolio rows: **39**
- exclusion rows: **242**
- no-lookahead failures: **0**

Average summary diagnostics:

- average universe count: **50**
- average excluded count: **18.62**
- average turnover: **0.43**

Top exclusion reasons in the current run:

1. `invalid_fcf`
2. `no_convergence`
3. `no_price_on_or_before`
4. `no_available_observation`
5. `invalid_shares`

This means performance should always be interpreted together with data coverage and exclusion rules.

## Thesis-safe conclusion draft

Suggested wording:

> In the current free-data implementation, a reverse DCF ranking strategy produced positive average active returns against the SET benchmark across 3-, 6-, and 12-month holding periods. The strongest average active return appeared in the 3-month horizon, while the highest hit rate appeared in the 6-month horizon. However, the result depends on free-data coverage, explicit exclusion rules, and a fixed-WACC historical scoring assumption, so the findings should be interpreted as evidence for this implementation rather than as universal proof of superiority.

## Recommended discussion points

### Why the strategy may work

- reverse DCF may identify names where market-implied growth is below realized historical business strength
- short-to-medium horizons may react faster to valuation gap normalization

### Sector appendix highlights

From `research_data/latest/backtest/sector_summary.csv`:

- **Technology** showed the strongest average active return in all three tested horizons in the current sample
- **Communication Services** also remained positive across all tested horizons
- **Financial Services** contributed the largest number of selections and stayed positive on average across horizons
- Several sectors, especially **Industrials** and **Basic Materials**, were materially weaker on average

This suggests the aggregate result is not uniform across sectors and should be discussed as a cross-sectional effect, not only as a market-wide average.

### WACC sensitivity highlights

From `research_data/latest/backtest/wacc_sensitivity.csv`:

- The strategy remained **positive on average** across the tested fixed-WACC assumptions of **6%, 8%, and 10%**
- The **6-month** and **12-month** active returns improved as the fixed WACC assumption increased in the current run
- The **3-month** result stayed positive across all tested WACC settings with only modest variation

This does not remove model risk, but it does show that the current result is not driven by only one narrow fixed-WACC value.

### Why the result may weaken

- free-data gaps reduce usable universe size
- fixed WACC is a simplification
- some sectors may behave differently from the aggregate result
- long-horizon results were weaker than short-horizon results

## Next analysis steps

1. break results down by sector
2. compare top-10 with decile portfolios
3. test sensitivity to fixed-WACC choices
4. test alternative rebalance schedules
5. add charts/tables for thesis presentation

## Appendix references

After running the extended analysis step, use:

- `research_data/latest/backtest/sector_summary.csv`
- `research_data/latest/backtest/wacc_sensitivity.csv`
- `research_data/latest/backtest/appendix.md`
- `research_data/latest/backtest/figures/active_return_by_horizon.png`
- `research_data/latest/backtest/figures/hit_rate_by_horizon.png`
- `research_data/latest/backtest/figures/sector_active_return_heatmap.png`
- `research_data/latest/backtest/figures/wacc_sensitivity.png`

to extend the thesis discussion with sector behavior and robustness checks.
