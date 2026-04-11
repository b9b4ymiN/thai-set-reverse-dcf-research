# Executive Summary

## Objective

This project evaluates whether a **fundamental-only reverse DCF strategy** can select Thai stocks that outperform the Thai market using **free data only**.

## Approach

The workflow built in this repository now includes:

1. a free-data research bundle based on Yahoo Finance / `yfinance`
2. dated quarterly and annual statement observations
3. a benchmark-relative reverse DCF backtest
4. explicit no-look-ahead audit artifacts
5. sector and WACC-sensitivity appendices

## Main result

In the current implementation, the reverse DCF strategy produced **positive average active return** versus the SET benchmark across all tested holding periods:

- **3 months:** +1.6818%
- **6 months:** +1.6514%
- **12 months:** +0.8502%

Hit rates were:

- **3 months:** 53.85%
- **6 months:** 69.23%
- **12 months:** 61.54%

## Interpretation

The current evidence supports a **positive empirical result for this implementation**, especially over short and medium holding periods.

However, this should be interpreted carefully:

- the workflow depends on free-data coverage
- the historical backtest uses a **fixed WACC assumption**
- exclusions and missing-data rules materially affect the final universe

So the result should be presented as:

> evidence that the current reverse DCF implementation can outperform the benchmark on average in the tested sample,
> not universal proof that reverse DCF always beats the market.

## Strengths of the current system

- free-data reproducibility
- explicit no-look-ahead controls
- benchmark-relative outputs
- exclusion transparency
- sector breakdown and WACC sensitivity analysis
- thesis-ready bundle generation

## Main limitations

1. fixed WACC is a simplifying assumption
2. Yahoo coverage gaps still constrain the investable universe
3. cross-sector behavior is uneven
4. this is a research workflow, not a production investment system

## Recommendation

For thesis presentation, the strongest framing is:

- emphasize **methodological transparency**
- report the positive benchmark-relative findings
- show the audit/exclusion/sensitivity evidence
- explicitly state the remaining model and data limitations
