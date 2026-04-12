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
| TTB.BK | 2023-03-31 | 2023-02-14 | 2023-03-31 | fixed | True | 45 |
| IVL.BK | 2023-03-31 | 2023-02-14 | 2023-03-31 | fixed | True | 45 |
| BBL.BK | 2023-03-31 | 2023-02-14 | 2023-03-31 | fixed | True | 45 |
| MINT.BK | 2023-03-31 | 2023-02-14 | 2023-03-31 | fixed | True | 45 |
| ADVANC.BK | 2023-03-31 | 2023-02-14 | 2023-03-31 | fixed | True | 45 |
| SCGP.BK | 2023-03-31 | 2023-02-14 | 2023-03-31 | fixed | True | 45 |
| TOP.BK | 2023-03-31 | 2023-02-14 | 2023-03-31 | fixed | True | 45 |
| CPALL.BK | 2023-03-31 | 2023-02-14 | 2023-03-31 | fixed | True | 45 |
| EGCO.BK | 2023-03-31 | 2023-02-14 | 2023-03-31 | fixed | True | 45 |
| BJC.BK | 2023-03-31 | 2023-02-14 | 2023-03-31 | fixed | True | 45 |
