# Q&A Sheet

## Q1. Why use reverse DCF instead of normal DCF?

Because reverse DCF is better suited to asking what the market is already pricing in.  
That makes it useful for testing whether expectations embedded in market prices are too high or too low.

## Q2. Why is this useful for stock selection?

If implied growth is much lower than realized business growth, the stock may reflect pessimistic expectations.  
That can create opportunity if the market later re-prices the stock.

## Q3. Why use free data?

The thesis requirement was to build a reproducible and accessible workflow without paid market data.  
That makes the result easier to repeat and extend in future projects.

## Q4. Why did you use Yahoo Finance as the primary source?

Because under the free-only constraint it gave the best balance of:

- historical coverage
- automation
- reuse across projects

Official SET pages remain useful for validation, but not as the core backtest datasource.

## Q5. How did you handle look-ahead bias?

I explicitly used:

- `Availability_Date <= Rebalance_Date`
- price on or before the rebalance date
- a no-look-ahead audit artifact
- fixed WACC mode in historical scoring

The latest audit reported **0 no-lookahead failures**.

## Q6. Why use fixed WACC?

Using the latest snapshot WACC historically would leak future information into earlier rebalance periods.  
Fixed WACC is a conservative simplification that reduces that leakage risk.

## Q7. Does this prove reverse DCF always beats the market?

No.  
It shows that in the **current implementation and sample**, the strategy produced positive average active return across the tested horizons.

That is evidence, not universal proof.

## Q8. What were the main results?

Active return vs benchmark:

- 3M: **+1.6818%**
- 6M: **+1.6514%**
- 12M: **+0.8502%**

Best hit rate:

- 6M: **69.23%**

## Q9. What are the main limitations?

1. free-data gaps
2. fixed WACC simplification
3. exclusions reduce the usable universe
4. cross-sector behavior is uneven

## Q10. Which sectors looked strongest?

In the current sample:

- Technology
- Communication Services
- Financial Services

These sectors contributed much of the stronger benchmark-relative behavior.

## Q11. How robust are the results to WACC assumptions?

The tested fixed-WACC sensitivity outputs at 6%, 8%, and 10% remained positive on average.  
That suggests the current result is not driven by only one narrow WACC assumption.

## Q12. What would you do next if you had more time?

1. richer sector-level tests
2. alternative rebalance rules
3. decile portfolios instead of only top-10
4. stronger historical parameter estimation
5. more formal thesis charts and tables
