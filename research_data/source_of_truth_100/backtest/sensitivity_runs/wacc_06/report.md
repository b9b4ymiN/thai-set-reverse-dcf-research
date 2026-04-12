# Reverse DCF Backtest Report

- Case: baseline
- Rebalance frequency: Q
- Horizons (months): [3, 6, 12]
- Top N portfolio: 10
- Daily stop-loss enabled: False
- Stop-loss pct: 0.0
- Buy ban threshold (losing buy rounds): 2
- Signals generated: 1048

## Summary

| Horizon_Months | Portfolio_Return | Benchmark_Return | Active_Return | Hit_Rate | Observations | Avg_Turnover | Avg_Universe_Count | Avg_Excluded_Count | Case_Name | Top_N | Stop_Loss_Pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | 0.017602860034581218 | 0.00021748368410908213 | 0.01738537635047214 | 55.00000000000001 | 20 | 0.73 | 100.0 | 47.6 | baseline | 10 | 0.0 |
| 6 | 0.01814162828128398 | 0.000834697836101811 | 0.01730693044518217 | 50.0 | 20 | 0.73 | 100.0 | 47.6 | baseline | 10 | 0.0 |
| 12 | 0.0116226570969695 | -0.00652341691141628 | 0.018146074008385776 | 30.0 | 20 | 0.73 | 100.0 | 47.6 | baseline | 10 | 0.0 |

---
**Methodology Note**: This backtest employs the Damodaran Stern Reverse DCF framework for growth implication analysis.
For detailed formula mapping and theoretical foundations, see `METHODOLOGY.md` and Damodaran's lecture materials on intrinsic valuation.
Framework Reference: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/home.htm
