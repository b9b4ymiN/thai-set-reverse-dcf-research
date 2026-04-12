# No-Lookahead Audit

- Case: damodaran
- WACC mode: damodaran
- No-lookahead failures: 0

This audit samples the first generated rebalance cross-section. Each sampled row should satisfy:
1. `Availability_Date <= Rebalance_Date`
2. `Price_Date <= Rebalance_Date`
3. backtest WACC mode is fixed (not latest snapshot)

| Ticker | Rebalance_Date | Availability_Date | Price_Date | WACC_Mode | No_Lookahead_Pass | Days_Since_Available |
| --- | --- | --- | --- | --- | --- | --- |
| GPI.BK | 2021-06-30 | 2021-05-15 | 2021-06-30 | damodaran | True | 46 |
| NCH.BK | 2021-06-30 | 2021-05-15 | 2021-06-30 | damodaran | True | 46 |
| RCL.BK | 2021-06-30 | 2021-05-15 | 2021-06-30 | damodaran | True | 46 |
| TVO.BK | 2021-06-30 | 2021-05-15 | 2021-06-30 | damodaran | True | 46 |
| DRT.BK | 2021-06-30 | 2021-05-15 | 2021-06-30 | damodaran | True | 46 |
| ADVANC.BK | 2021-06-30 | 2021-05-15 | 2021-06-30 | damodaran | True | 46 |
| PF.BK | 2021-06-30 | 2021-05-15 | 2021-06-30 | damodaran | True | 46 |
| SPRC.BK | 2021-06-30 | 2021-05-15 | 2021-06-30 | damodaran | True | 46 |
| EGCO.BK | 2021-06-30 | 2021-05-15 | 2021-06-30 | damodaran | True | 46 |
| STPI.BK | 2021-06-30 | 2021-05-15 | 2021-06-30 | damodaran | True | 46 |
