# Presentation Script

## Slide 1 — Research question

This project asks whether a **fundamental-only reverse DCF strategy** can select Thai stocks that outperform the Thai market benchmark using only **free data**.

## Slide 2 — Why reverse DCF

Instead of assuming growth and asking what a stock is worth, reverse DCF starts from the market price and asks:

> what growth is the market already implying?

Then the strategy compares implied growth with observed business performance.

## Slide 3 — Data and workflow

The workflow in this repository now includes:

1. free-data acquisition from Yahoo Finance / `yfinance`
2. dated quarterly and annual statement observations
3. price and benchmark history
4. reverse DCF signal construction
5. benchmark-relative backtesting
6. no-look-ahead audit and exclusion reporting

## Slide 4 — Signal definition

For each rebalance date:

- choose the latest observation where `Availability_Date <= Rebalance_Date`
- solve the implied growth from price and DCF inputs
- compute:

`Signal_Score = Actual_Revenue_Growth - Implied_Growth_Rate`

Higher score means realized growth is stronger than what the market price appears to imply.

## Slide 5 — Backtest design

- Rebalance frequency: quarterly
- Portfolio: equal-weight top 10 names
- Horizons: 3, 6, 12 months
- Benchmark: SET index (`^SET.BK`)
- Historical WACC mode: fixed

## Slide 6 — Main results

Average active return versus benchmark:

- 3 months: **+1.6818%**
- 6 months: **+1.6514%**
- 12 months: **+0.8502%**

Hit rates:

- 3 months: **53.85%**
- 6 months: **69.23%**
- 12 months: **61.54%**

## Slide 7 — Audit and robustness

The workflow also produced:

- no-look-ahead failures: **0**
- explicit exclusion report
- sector breakdown
- WACC sensitivity analysis

This means the result is not only a return number; it is supported by process evidence.

## Slide 8 — Sector and sensitivity insight

In the current sample:

- Technology was strongest across horizons
- Communication Services also remained positive
- Financial Services contributed many selections and stayed positive on average
- WACC sensitivity stayed positive across tested fixed assumptions

## Slide 9 — Limitations

Important limitations:

- fixed WACC is a simplification
- free Yahoo data can have gaps
- exclusions affect the usable universe
- results should not be overstated beyond the tested implementation

## Slide 10 — Conclusion

The current evidence suggests that a reverse DCF stock-selection strategy can outperform the Thai market benchmark on average in this tested sample.

But the proper thesis conclusion is:

> reverse DCF shows promising empirical performance in this free-data implementation, while remaining subject to data coverage, modeling assumptions, and robustness limits.
