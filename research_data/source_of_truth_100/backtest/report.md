# Reverse DCF Backtest Report

- Case: baseline
- Rebalance frequency: Q
- Horizons (months): [3, 6, 12]
- Top N portfolio: 10
- Daily stop-loss enabled: False
- Stop-loss pct: 0.0
- Buy ban threshold (losing buy rounds): 2
- Signals generated: 116

## Summary

| Horizon_Months | Portfolio_Return | Benchmark_Return | Active_Return | Hit_Rate | Observations | Avg_Turnover | Avg_Universe_Count | Avg_Excluded_Count | Case_Name | Top_N | Stop_Loss_Pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | 0.005006237315212933 | 0.011078802234925574 | -0.006072564919712638 | 46.666666666666664 | 15 | 0.2967195767195767 | 100.0 | 92.26666666666667 | baseline | 10 | 0.0 |
| 6 | 0.010039559665020808 | 0.015642847463142633 | -0.005603287798121827 | 60.0 | 15 | 0.2967195767195767 | 100.0 | 92.26666666666667 | baseline | 10 | 0.0 |
| 12 | 0.03382593891157029 | 0.0018632038810876199 | 0.03196273503048267 | 46.666666666666664 | 15 | 0.2967195767195767 | 100.0 | 92.26666666666667 | baseline | 10 | 0.0 |

---
**Methodology Note**: This backtest employs the Damodaran Stern Reverse DCF framework for growth implication analysis.
For detailed formula mapping and theoretical foundations, see `METHODOLOGY.md` and Damodaran's lecture materials on intrinsic valuation.
Framework Reference: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/home.htm
