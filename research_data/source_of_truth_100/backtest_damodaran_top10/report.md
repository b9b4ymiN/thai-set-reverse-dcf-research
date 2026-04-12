# Reverse DCF Backtest Report

- Case: damodaran
- Rebalance frequency: Q
- Horizons (months): [3, 6, 12]
- Top N portfolio: 10
- Daily stop-loss enabled: False
- Stop-loss pct: 0.0
- Buy ban threshold (losing buy rounds): 2
- Signals generated: 1028

## Summary

| Horizon_Months | Portfolio_Return | Benchmark_Return | Active_Return | Hit_Rate | Observations | Avg_Turnover | Avg_Universe_Count | Avg_Excluded_Count | Case_Name | Top_N | Stop_Loss_Pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | 0.013620712271360146 | 0.00021748368410908213 | 0.013403228587251065 | 55.00000000000001 | 20 | 0.6799999999999999 | 100.0 | 48.6 | damodaran | 10 | 0.0 |
| 6 | 0.020534923954225043 | 0.000834697836101811 | 0.01970022611812323 | 60.0 | 20 | 0.6799999999999999 | 100.0 | 48.6 | damodaran | 10 | 0.0 |
| 12 | 0.014907251819725336 | -0.00652341691141628 | 0.021430668731141616 | 40.0 | 20 | 0.6799999999999999 | 100.0 | 48.6 | damodaran | 10 | 0.0 |

---
**Methodology Note**: This backtest employs the Damodaran Stern Reverse DCF framework for growth implication analysis.
For detailed formula mapping and theoretical foundations, see `METHODOLOGY.md` and Damodaran's lecture materials on intrinsic valuation.
Framework Reference: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/home.htm
