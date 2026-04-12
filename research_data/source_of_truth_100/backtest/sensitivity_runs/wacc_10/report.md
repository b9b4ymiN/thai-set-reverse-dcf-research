# Reverse DCF Backtest Report

- Case: baseline
- Rebalance frequency: Q
- Horizons (months): [3, 6, 12]
- Top N portfolio: 10
- Daily stop-loss enabled: False
- Stop-loss pct: 0.0
- Buy ban threshold (losing buy rounds): 2
- Signals generated: 1007

## Summary

| Horizon_Months | Portfolio_Return | Benchmark_Return | Active_Return | Hit_Rate | Observations | Avg_Turnover | Avg_Universe_Count | Avg_Excluded_Count | Case_Name | Top_N | Stop_Loss_Pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | 0.017171497275587897 | 0.00021748368410908213 | 0.016954013591478818 | 65.0 | 20 | 0.72 | 100.0 | 49.65 | baseline | 10 | 0.0 |
| 6 | 0.01953853561570145 | 0.000834697836101811 | 0.018703837779599643 | 55.00000000000001 | 20 | 0.72 | 100.0 | 49.65 | baseline | 10 | 0.0 |
| 12 | 0.019807455081489914 | -0.00652341691141628 | 0.026330871992906197 | 40.0 | 20 | 0.72 | 100.0 | 49.65 | baseline | 10 | 0.0 |

---
**Methodology Note**: This backtest employs the Damodaran Stern Reverse DCF framework for growth implication analysis.
For detailed formula mapping and theoretical foundations, see `METHODOLOGY.md` and Damodaran's lecture materials on intrinsic valuation.
Framework Reference: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/home.htm
