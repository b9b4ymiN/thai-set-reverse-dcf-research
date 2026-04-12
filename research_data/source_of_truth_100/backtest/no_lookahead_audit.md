# No-Lookahead Audit

- Case: baseline
- WACC mode: fixed
- No-lookahead failures: 0

This audit samples the first generated rebalance cross-section. Each sampled row should satisfy:
1. `Availability_Date <= Rebalance_Date`
2. `Price_Date <= Rebalance_Date`
3. backtest WACC mode is fixed (not latest snapshot)

| Ticker | Rebalance_Date | Availability_Date | Price_Date | WACC_Mode | No_Lookahead_Pass | Days_Since_Available |
| --- | --- | --- | --- | --- | --- | --- |
| BCT.BK | 2022-06-30 | 2022-05-15 | 2022-06-30 | fixed | True | 46 |
