# Reverse DCF Backtest Report

- Case: damodaran
- Rebalance frequency: Q
- Horizons (months): [3, 6, 12]
- Top N portfolio: 5
- Daily stop-loss enabled: False
- Stop-loss pct: 0.0
- Buy ban threshold (losing buy rounds): 2
- Signals generated: 1077

## Summary

| Horizon_Months | Portfolio_Return | Benchmark_Return | Active_Return | Hit_Rate | Observations | Avg_Turnover | Avg_Universe_Count | Avg_Excluded_Count | Case_Name | Top_N | Stop_Loss_Pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | -0.014185983383424847 | 0.00021748368410908213 | -0.01440346706753393 | 40.0 | 20 | 0.76 | 100.0 | 46.15 | damodaran | 5 | 0.0 |
| 6 | -0.022861795270235886 | 0.000834697836101811 | -0.023696493106337695 | 40.0 | 20 | 0.76 | 100.0 | 46.15 | damodaran | 5 | 0.0 |
| 12 | -0.05857220071037389 | -0.00652341691141628 | -0.05204878379895761 | 25.0 | 20 | 0.76 | 100.0 | 46.15 | damodaran | 5 | 0.0 |

---
**Methodology Note**: This backtest employs the Damodaran Stern Reverse DCF framework for growth implication analysis.
For detailed formula mapping and theoretical foundations, see `METHODOLOGY.md` and Damodaran's lecture materials on intrinsic valuation.
Framework Reference: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/home.htm
