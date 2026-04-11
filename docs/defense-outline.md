# Defense Outline

## 1. Opening

My thesis studies whether a **fundamental-only reverse DCF strategy** can select Thai stocks that outperform the SET benchmark using **free data only**.

## 2. Motivation

Traditional DCF starts with an assumed growth rate and estimates value.

Reverse DCF asks the opposite question:

> what growth is already embedded in the current market price?

That makes it useful for testing whether market expectations are too pessimistic or too optimistic.

## 3. Core contribution

This project contributes:

1. a free-data Thai equity research pipeline
2. dated quarterly and annual fundamental observations
3. a benchmark-relative reverse DCF backtest
4. explicit no-look-ahead audit artifacts
5. sensitivity and sector appendix outputs

## 4. Method

At each rebalance date:

1. choose the latest observation where `Availability_Date <= Rebalance_Date`
2. use the latest available adjusted price on or before the rebalance date
3. solve reverse DCF implied growth
4. compute  
   `Signal_Score = Actual_Revenue_Growth - Implied_Growth_Rate`
5. form an equal-weight top-10 portfolio
6. compare portfolio returns against the SET benchmark over 3, 6, and 12 months

## 5. Controls against bias

The workflow includes:

- dated `Availability_Date`
- no-look-ahead audit output
- explicit exclusion reporting
- fixed WACC mode in backtesting to avoid leaking latest snapshot assumptions into historical periods

## 6. Main findings

Average active return versus benchmark:

- 3 months: **+1.6818%**
- 6 months: **+1.6514%**
- 12 months: **+0.8502%**

Hit rates:

- 3 months: **53.85%**
- 6 months: **69.23%**
- 12 months: **61.54%**

## 7. Interpretation

The evidence suggests that the current reverse DCF implementation can outperform the benchmark on average in the tested sample.

But the correct claim is **conditional**, not absolute:

- conditional on free-data coverage
- conditional on exclusion rules
- conditional on fixed-WACC historical scoring

## 8. Robustness discussion

Additional outputs show:

- no-look-ahead failures: **0**
- strong sector variation
- positive WACC sensitivity results across tested fixed assumptions

So the result is not based on a single isolated number.

## 9. Limitations

1. Yahoo free-data coverage is imperfect
2. fixed WACC is a simplification
3. some sectors behave much better than others
4. this is a research implementation, not a full production portfolio system

## 10. Final conclusion

My conclusion is:

> reverse DCF shows promising benchmark-relative performance in this Thai free-data implementation, while still requiring careful interpretation due to data coverage and modeling assumptions.
