# Damodaran NYU Stern Datasets for Thai SET Reverse DCF

Source page: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datacurrent.html  
Page date: January 9, 2026  
Country risk update used here: `ctrypremApr26.xlsx` dated April 1, 2026  
Emerging-market beta/WACC files used here: `betaemerg.xls`, `waccemerg.xls`, both dated January 5, 2026  
ERP history files used here: `histimpl.xls` and `histretSP.xls`

## Scope

This note covers four Damodaran dataset groups that are directly useful for Thai SET reverse DCF and backtesting:

1. Thailand country risk premium
2. Emerging-market industry betas
3. Emerging-market WACC benchmarks by industry
4. Historical ERP datasets

The goal is not to copy the spreadsheets. The goal is to extract the parts that matter for valuation methodology and show how to apply them to Thai stocks without introducing avoidable lookahead bias.

## 1. Thailand Country Risk Premium (`ctrypremApr26.xlsx`)

### What the dataset is doing

Damodaran starts with a mature-market equity risk premium and then adds a country-specific premium.

Core logic:

- Mature-market ERP starts from the implied US equity risk premium.
- Country default spread is estimated from sovereign rating and/or CDS spreads.
- Country risk premium can be a default-spread number or an equity-adjusted number.
- Total country ERP = mature-market ERP + country risk premium.

The worksheet states:

- Mature-market ERP input: `4.77%`
- US ERP input: `5.03%`
- Equity-volatility multiplier: `1.5344`

### Thailand values extracted

Thailand row in `ERPs by country`:

- Moody's rating: `Baa1`
- Rating-based default spread: `1.5211%`
- Total equity risk premium using rating approach: `7.1039%`
- Country risk premium using rating approach: `2.3339%`
- Sovereign CDS net of Swiss CDS: `0.72%`
- Total equity risk premium using CDS approach: `5.8748%`
- Country risk premium using CDS approach: `1.1048%`

Thailand row in `Regional Weighted Averages`:

- 2024 GDP weight in Asia bucket: `1.516%`
- Corporate tax rate: `20%`

### Methodology takeaway

There are really two usable Thailand ERPs in the sheet:

- `5.8748%` from the CDS-based route
- `7.1039%` from the rating-based route

That spread is meaningful. It is the difference between a more market-linked view of sovereign risk and a more ratings-based view.

### How to apply to Thai SET stocks

Use this file for the **equity risk premium**, not as a full WACC by itself.

Recommended use:

- For live Thai valuation in THB:
  - `Cost of Equity = Thai risk-free rate + Levered Beta x Thailand ERP`
- For USD-framed cross-market comparison:
  - `Cost of Equity = US$ risk-free rate + Levered Beta x Thailand ERP`
- Use `CDS-based ERP` as the base case if you want the premium to respond faster to market pricing.
- Use `rating-based ERP` as a conservative sensitivity case.

For this repo's reverse DCF work:

- Do not apply the April 1, 2026 Thailand ERP directly to older rebalance dates in the historical backtest.
- If a historical-country-risk series is not available, keep using fixed-WACC historical scoring or build a year-specific ERP table from archived Damodaran files.
- Thesis-ready sensitivity framing:
  - Base: Thailand CDS ERP
  - Conservative: Thailand rating ERP
  - Simple backtest control: fixed WACC

## 2. Emerging-Market Industry Betas (`betaemerg.xls`)

### What the dataset is doing

This file provides industry-level business-risk anchors across `96` emerging-market industries.

The sheet explains the mechanics:

- Raw beta is a simple average of firm betas.
- Betas combine 2-year and 5-year weekly regression betas, with heavier weight on 2-year when both exist.
- Debt includes lease debt.
- Unlevered beta removes financing effects using debt/equity and tax rate.
- Cash-adjusted unlevered beta strips out excess cash drag.

Spreadsheet settings used in the January 5, 2026 file:

- Tax setting for unlevering: `Marginal`
- Marginal tax rate input: `24.71%`

Cross-section summary from the 96-industry table:

- Median levered beta: `0.9414`
- Median unlevered beta: `0.7211`
- Median cash/firm value: `8.31%`
- Median equity standard deviation: `39.76%`

### Why this matters

For Thai stocks, the most portable output here is **unlevered beta**.

That lets you:

1. pick the closest operating/business bucket,
2. remove Damodaran's capital-structure assumptions,
3. relever using the Thai company's own debt mix and tax assumptions.

### Thai SET application rule

Recommended sequence:

1. Map each SET stock to the closest Damodaran industry bucket.
2. Start from `Unlevered beta`.
3. Relever with Thai company debt/equity:
   - `Levered Beta = Unlevered Beta x (1 + (1 - tax) x D/E)`
4. If the company holds unusually large net cash, consider the cash-corrected version instead of the plain unlevered beta.

### Example mapping for common SET100 industries

These are not "official" mappings. They are practical proxies for Thai reverse DCF work:

| SET100 industry in repo | Damodaran emerging-market proxy | Firms | Levered beta | Unlevered beta |
| --- | --- | ---: | ---: | ---: |
| Banks - Regional | Banks (Regional) | 104 | 0.6040 | 0.1192 |
| Telecom Services | Telecom. Services | 142 | 0.7144 | 0.5735 |
| Real Estate - Development | Real Estate (Development) | 786 | 0.9590 | 0.3865 |
| Medical Care Facilities | Hospitals/Healthcare Facilities | 164 | 0.7169 | 0.6198 |
| Oil & Gas Refining & Marketing | Oil/Gas (Integrated) | 15 | 0.7885 | 0.7043 |
| Packaged Foods | Food Processing | 1030 | 0.7204 | 0.5602 |
| Utilities - Independent Power Producers | Utility (General) | 14 | 0.6989 | 0.5480 |
| Lodging | Hotel/Gaming | 427 | 0.7044 | 0.5250 |
| Beverages - Non-Alcoholic | Beverage (Soft) | 40 | 0.5709 | 0.5501 |
| Packaging & Containers | Packaging & Container | 341 | 0.7397 | 0.5618 |
| Home Improvement Retail | Retail (Building Supply) | 55 | 0.7846 | 0.6224 |

### Practical guidance for Thai stocks

- Use direct firm beta only when the stock has deep trading history and acceptable liquidity.
- For thinly traded or noisy Thai names, prefer bottom-up beta from Damodaran industry betas.
- For conglomerates, build a segment-weighted beta rather than forcing a single bucket.
- For banks and insurers, treat industrial-style D/E formulas carefully because financial leverage is part of the business model.

## 3. Emerging-Market WACC Benchmarks (`waccemerg.xls`)

### What the dataset is doing

This file turns the emerging-market industry beta set into hurdle-rate benchmarks.

The January 5, 2026 worksheet uses these top-level inputs:

- Long-term Treasury bond rate: `3.95%`
- Equity risk premium input: `6.62%`
- Global default spread added to cost of debt: `1.57%`
- Marginal tax rate for debt shield: `25.11%`
- Expected inflation in local currency: `7.50%`
- Expected inflation in US$: `2.50%`

The sheet's structure is:

- `Cost of Equity = Risk-free rate + Beta x ERP`
- `Cost of Debt` is estimated from equity volatility using a spread lookup table
- `After-tax Cost of Debt = Cost of Debt x (1 - tax rate)`
- `Cost of Capital = E/V x Cost of Equity + D/V x After-tax Cost of Debt`
- `Cost of Capital (Local Currency)` converts the US$ hurdle rate into local currency using inflation assumptions

Cross-section summary from the 96-industry table:

- Median cost of equity: `10.18%`
- Median cost of debt: `6.41%`
- Median debt weight `D/(D+E)`: `24.47%`
- Median cost of capital in US$: `8.64%`
- Median cost of capital in local currency: `13.94%`

### Why this matters

This is the cleanest external benchmark for saying whether a Thai-stock WACC looks plausible.

It is most useful as:

- a prior,
- a sanity-check band,
- a sector-relative hurdle-rate benchmark,
- a starting point for sensitivity cases.

It is less useful as a plug-and-play final WACC because the sheet is not Thailand-specific by default.

### Example industry benchmark ranges for common SET100 groups

| SET100 industry in repo | Damodaran proxy | Cost of equity (US$) | Cost of capital (US$) | Cost of capital (local-currency converted) |
| --- | --- | ---: | ---: | ---: |
| Banks - Regional | Banks (Regional) | 7.95% | 5.08% | 10.20% |
| Telecom Services | Telecom. Services | 8.68% | 7.72% | 12.98% |
| Real Estate - Development | Real Estate (Development) | 10.30% | 6.65% | 11.85% |
| Medical Care Facilities | Hospitals/Healthcare Facilities | 8.70% | 8.02% | 13.29% |
| Oil & Gas Refining & Marketing | Oil/Gas (Integrated) | 9.17% | 8.57% | 13.87% |
| Packaged Foods | Food Processing | 8.72% | 7.64% | 12.89% |
| Utilities - Independent Power Producers | Utility (General) | 8.58% | 7.50% | 12.74% |
| Lodging | Hotel/Gaming | 8.61% | 7.42% | 12.66% |
| Beverages - Non-Alcoholic | Beverage (Soft) | 7.73% | 7.58% | 12.82% |
| Packaging & Containers | Packaging & Container | 8.85% | 7.65% | 12.90% |

### How to apply to Thai SET stocks

Recommended hierarchy:

1. Use Damodaran WACC as a sector anchor.
2. Replace the ERP with the Thailand ERP from `ctrypremApr26.xlsx`.
3. Replace debt weights with firm-specific capital structure.
4. Replace tax rate with Thailand statutory or normalized firm tax.
5. If valuing in THB, use a THB risk-free rate and THB-consistent assumptions.

For this repo's backtest:

- Keep fixed-WACC backtests as the no-lookahead baseline.
- Use Damodaran sector WACC only for supplementary sensitivity or out-of-sample robustness tests.
- A good thesis framing is:
  - fixed WACC backtest for historical integrity,
  - sector benchmark WACC for cross-sectional realism,
  - Thailand ERP sensitivity for current-snapshot valuation.

## 4. Historical ERP Data

There are two different ideas here, and they should not be mixed casually.

### 4.1 `histimpl.xls`: implied ERP history

This file is forward-looking. It backs out the ERP that would justify the market level, given cash yields, growth assumptions, and bond yields.

Important source caveat:

- The current data page is dated January 9, 2026.
- The downloaded `histimpl.xls` file itself reports `Date updated: 2024-01-05`.
- The sheet still includes a `2025` row and long-period summary rows.

Useful extracted points from the file:

- 2025 implied ERP (FCFE): `4.23%`
- 2025 T-bond rate: `4.18%`
- 1960-2025 average implied ERP: `4.2477%`
- 2006-2025 average implied ERP: `5.1580%`
- 2016-2025 average implied ERP: `4.9990%`

Methodology use:

- This is the best anchor for a forward-looking mature-market ERP.
- Damodaran uses this logic upstream in the country-risk spreadsheet.
- For Thai work, use it indirectly via the Thailand country-risk workbook unless you are rebuilding the country ERP stack yourself.

### 4.2 `histretSP.xls`: historical realized return premia

This file is backward-looking. It reports realized returns on US equities, bills, bonds, real estate, and gold, then derives historical premia.

Key extracted points:

- File date: `2025-01-01`
- Current estimator cell in the sheet: `5.4831%`
- Arithmetic equity risk premium, stocks minus T-bills:
  - `4.3778%` for 1928-2025
  - `5.3205%` for 1976-2025
  - `6.5876%` for 2016-2025
- Geometric equity risk premium, stocks minus T-bills:
  - `4.1980%` for 1928-2025
  - `5.1654%` for 1976-2025
  - `6.4920%` for 2016-2025

Methodology use:

- This is a history-based reasonableness check.
- It is not a direct Thailand ERP.
- It is useful for setting broad sensitivity ranges and defending why a chosen ERP is not absurdly low or high.

## Recommended Use in This Repo

### For current-snapshot Thai reverse DCF

Use:

- Thailand ERP from `ctrypremApr26.xlsx`
- bottom-up industry beta from `betaemerg.xls`
- firm-specific debt/cash/tax structure from the repo fundamentals

Suggested formula flow:

1. Choose Thai ERP:
   - base: CDS-based Thailand ERP
   - conservative: rating-based Thailand ERP
2. Choose industry unlevered beta from the nearest Damodaran bucket.
3. Relever beta using Thai firm capital structure.
4. Estimate cost of equity using Thai-consistent risk-free rate.
5. Build WACC using firm debt mix and normalized tax rate.

### For historical backtesting

Do not use the latest Damodaran country or sector numbers retroactively across the entire backtest window.

Safer choices:

- keep fixed WACC for the baseline test,
- or build a year-specific Damodaran snapshot table and lag it properly,
- or test a small number of coarse historical regimes rather than a continuously updated modern WACC.

### Thesis-ready framing

These Damodaran datasets are best used as:

- a methodology defense for ERP and beta construction,
- a current-valuation anchor for Thai stocks,
- a sensitivity framework around the repo's fixed-WACC backtest,
- and evidence that sector/business risk should not be treated as identical across the SET universe.

They are not, by themselves, enough to justify a leakage-prone historical WACC series.

## Bottom Line

- `ctrypremApr26.xlsx` is the key file for Thailand-specific ERP.
- `betaemerg.xls` is the key file for bottom-up Thai stock beta estimation.
- `waccemerg.xls` is best used as a sector sanity-check and sensitivity benchmark.
- `histimpl.xls` and `histretSP.xls` help justify the mature-market ERP range, but they are not direct Thailand inputs.
- For this repo, the cleanest integration is:
  - Damodaran for current-snapshot valuation assumptions,
  - fixed-WACC or lagged annual assumptions for historical backtesting.
