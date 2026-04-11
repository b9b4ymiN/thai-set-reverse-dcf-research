# Reverse DCF as a Value Investing Framework for Thai SET Markets

Authorial note: This thesis adopts a framework-first, valuation-centered style inspired by Professor Aswath Damodaran's teaching approach, but the analysis, evidence, and wording are specific to this repository and its artifacts.

## Abstract

This thesis evaluates whether a reverse discounted cash flow framework can be used as a practical value investing tool in Thai equity markets. The central idea is simple: instead of forecasting growth and deriving value, we begin with market price and solve backward for the growth expectations embedded in that price. In a market such as Thailand, where cross-sectional differences in quality, leverage, liquidity, and cyclicality are large, that inversion can be useful because it forces the investor to ask a disciplined question: what narrative is the market already pricing in, and is that narrative too pessimistic or too optimistic relative to business fundamentals?

The repository supporting this thesis contains two distinct empirical layers. The first is an earlier broad-study lane built around a large Thai-stock universe and a simplified reverse DCF ranking simulation. Its saved output reports a 15.68% compound annual growth rate and a 93.1% win rate for a top-20 portfolio, but that lane is best interpreted as an exploratory research artifact rather than a point-in-time audited backtest. The second is a stricter thesis bundle built from dated fundamental observations, explicit availability dates, historical price series, benchmark-relative return measurement, and no-lookahead audit outputs. That audited bundle covers 50 Thai equities, 536 dated annual and quarterly observations, and 13 quarterly rebalance dates from March 31, 2023 through March 31, 2026. In that stricter design, the reverse DCF ranking strategy produced positive average active returns against the SET benchmark over 3-, 6-, and 12-month horizons, with zero no-lookahead failures in the latest audit artifact.

The core conclusion of the thesis is not that reverse DCF is a magic formula for Thai stocks. It is narrower and more defensible. Reverse DCF appears to be a useful organizing framework for Thai value investing because it turns valuation into a comparison between market-implied expectations and observed operating reality. In the repository's stricter backtest, that framework generates positive benchmark-relative evidence across all tested holding periods. However, the result remains conditional on free-data coverage, fixed-WACC historical scoring, explicit exclusions, and a relatively short audited sample window. The framework is therefore best viewed as a disciplined starting point for fundamental investing in Thai markets, not as proof of universal or persistent alpha.

## Executive Summary

The thesis asks a practical question: can reverse DCF help investors identify mispriced Thai equities better than conventional screening ratios alone? In developed markets, the attraction of reverse DCF is that it strips away some of the illusion of precision embedded in conventional DCF models. In emerging markets, that attraction is even stronger. When country risk, sector cyclicality, financing structure, and disclosure quality vary across firms, the most dangerous valuation input is often the one the analyst pretends to know with confidence. Reverse DCF is useful because it converts price into an implied story and allows the investor to judge whether that story is plausible.

The Thai market is a good setting for this question. It is large enough to offer cross-sectional sector diversity, but narrow enough that broad country-level risk, macro regime shifts, financing conditions, and benchmark structure matter materially. A Thai investor cannot value companies as though they were U.S. firms with identical equity risk premiums and financing conditions. The country risk premium, the local currency framework, the industry composition of the market, and the uneven availability of long historical data all matter. That is why this thesis relies heavily on Damodaran's country risk and industry beta datasets, but refuses to import those numbers mechanically into historical backtests. For historical ranking, the methodology deliberately uses a fixed-WACC baseline to reduce lookahead bias. For interpretation, live Thai country risk estimates from Damodaran are used as valuation context and sensitivity anchors.

Three headline findings emerge.

First, the audited no-lookahead thesis bundle provides positive evidence for the framework. Using a quarterly top-10 equal-weight strategy and a fixed WACC assumption, the portfolio outperformed the SET benchmark on average in all tested horizons: 1.68% active return over 3 months, 1.65% over 6 months, and 0.85% over 12 months. Hit rates were 53.85%, 69.23%, and 61.54%, respectively. No lookahead failures were recorded in the latest audit file.

Second, sector behavior matters. Technology, communication services, and financial services were stronger contributors in the latest appendix outputs, while industrials and basic materials were materially weaker. That is exactly the kind of result a serious valuation investor should expect. Reverse DCF is not a universal market-timing device. It is a cross-sectional expectations framework, and the usefulness of expectations gaps will vary by sector structure, cyclicality, and accounting quality.

Third, evidence quality matters more than headline returns. The broader saved simulation artifact in `backtest_results/metrics_20260411_133531.txt` reports a 15.68% CAGR and a 93.1% win rate, but those outputs come from a simplified simulation path rather than the repository's stricter dated backtest pipeline. A disciplined thesis should not blur the two. The correct interpretation is that the broader study is encouraging, while the audited bundle is the stronger evidence base.

For practitioners, the payoff is practical. Reverse DCF can serve as a value investing framework for Thai equities if it is used with four disciplines: use market price to infer expectations, compare those expectations to operating reality, anchor discount rates in country and sector risk, and be explicit about what the data can and cannot prove. The moment the framework is treated as a black box, it stops being value investing and becomes parameter theater.

## 1. Introduction: Value Investing in Emerging Markets

Value investing begins with a simple proposition: price and value are not the same thing. But that proposition becomes harder to implement in emerging markets than in mature markets because the errors investors make are larger and more varied. In an emerging market, the analyst has to deal not only with business quality and competitive advantage, but also with country risk, currency risk, political uncertainty, disclosure unevenness, family control, cyclical financing structures, and sectors where accounting numbers are less informative than they appear.

Thailand is a case in point. The SET contains mature cash-generating businesses, financially engineered firms, regulated utilities, cyclical commodity names, banks where free cash flow is conceptually awkward, and consumer businesses where growth narratives can swing from sobriety to fantasy very quickly. A price-to-earnings screen can identify apparently cheap stocks, but it will not tell us what growth or operating performance is already embedded in those prices. A low multiple can reflect undervaluation, but it can also reflect deteriorating economics, weak governance, capital intensity, or a market that correctly sees trouble ahead.

That is where reverse DCF becomes useful. A conventional DCF invites the analyst to forecast revenue growth, margins, reinvestment, and discount rates, then arrive at an intrinsic value. The problem is that the precision of that exercise is often fake. If the analyst's growth assumption is unmoored from what the market is already pricing in, the model turns into a machine for confirming prior beliefs. Reverse DCF flips the exercise. It uses market price as the output and solves for the growth rate or performance assumption that would justify that price. Once the implied expectation is extracted, the real work begins: deciding whether the market's story is too pessimistic or too optimistic.

This inversion is particularly attractive in Thai markets for three reasons.

First, country and sector risk matter enough that discount-rate discipline is essential. A Thai valuation framework that simply borrows a mature-market equity risk premium is not serious. The Damodaran country risk data used in this repository show that Thailand's total equity risk premium can reasonably be framed at 5.8748% using a CDS-based route or 7.1039% using a rating-based route. That spread is not cosmetic. It reflects the fact that country risk can be framed more optimistically or more conservatively, and any Thai valuation framework that ignores that choice is pretending that risk is static when it is not.

Second, expectations matter more in markets with uneven disclosure and heterogeneous business quality. The same low multiple means different things for a regional bank, a commodity refiner, a hospital, a property developer, and a telecom operator. Reverse DCF forces the analyst to compare price-implied expectations with the economic reality of each business instead of assuming that all cheap stocks are cheap for the same reason.

Third, emerging markets punish overfitting. The more fragile the data, the more dangerous it becomes to optimize a strategy until it looks good in-sample. The proper response is not to abandon quantitative structure; it is to simplify the framework, state assumptions clearly, and keep a skeptical eye on what the numbers are really saying. That is the spirit in which this thesis is written.

### 1.1 Research Question

The thesis asks:

Can a reverse DCF ranking framework, implemented with free data and controlled for obvious lookahead bias, identify Thai equities that outperform the SET benchmark over investable holding periods?

This question matters because most value investing frameworks in emerging markets fail in one of two ways. They are either too qualitative to be tested rigorously, or too quantitative to acknowledge the fragility of their assumptions. Reverse DCF sits in the middle. It is quantitative enough to structure ranking and portfolio formation, but qualitative enough to force interpretation about whether implied expectations are realistic.

### 1.2 Thesis Contribution

This thesis contributes in five ways.

First, it adapts reverse DCF to Thai SET markets using a country-risk-aware but historically bias-conscious framework.

Second, it separates exploratory evidence from stricter audited evidence. That distinction is critical because research credibility depends not just on the strength of results, but on the integrity of the design that produced them.

Third, it shows how Damodaran's valuation principles can be localized for an emerging market without blindly importing latest-available parameters into historical tests.

Fourth, it documents free-data constraints explicitly. The thesis does not assume access to premium Thai market terminals. That makes the workflow more reproducible but also more imperfect, which is exactly the tradeoff real analysts face.

Fifth, it provides a practical framework for investors. The goal is not just academic validity. It is to create a repeatable way to think about market expectations, business fundamentals, and valuation gaps in Thailand.

### 1.3 Why Thai SET Markets Are a Useful Testing Ground

Thai markets provide an unusual combination of characteristics.

- They include a meaningful mix of banks, property developers, utilities, consumer franchises, industrial exporters, hospitals, and energy firms.
- Country risk is not trivial, so discount-rate assumptions matter.
- Many stocks are large enough to be investable, but the market is not so deep that inefficiency is impossible.
- Free-data coverage exists, but it is incomplete and uneven, which mirrors the real constraints faced by many independent investors.

In short, Thailand is neither a frictionless U.S.-style market nor a tiny illiquid frontier exchange. It is exactly the kind of market where a disciplined expectations framework has a chance to add value, but only if it respects the market's structural frictions.

### 1.4 Why Conventional Thai Value Screens Are Not Enough

The case for reverse DCF becomes stronger once we ask what conventional Thai value screens miss.

A low P/E stock can be cheap because the market has underappreciated normalized earnings power. It can also be cheap because earnings are cyclically high, because capital needs are being hidden by accounting timing, because leverage is too high, or because governance and capital allocation deserve a discount. A high dividend yield can signal disciplined cash distribution, but it can also signal the absence of reinvestment opportunities. A low price-to-book ratio can be attractive in banks and property firms, but it can also indicate that the market doubts asset quality or future returns on equity.

These are not problems with the ratios themselves. They are problems with using the ratios without a narrative framework. Reverse DCF improves the screen because it asks a better second question. Once a stock appears cheap, what growth and operating performance is the market assuming? If the implied expectation is only mildly demanding and the business is fragile, the stock may not be cheap at all. If the implied expectation is severely pessimistic and the business is merely stable, the stock may be attractive even if conventional ratios do not shout it.

Thai markets are full of names where this distinction matters. Property developers can look cheap for years because the market distrusts inventory conversion and leverage. Financials can trade at compressed multiples because investors fear credit stress or regulatory drag. Consumer and communication names can look fully priced even when their implied growth assumptions are not extreme. A reverse DCF lens is useful because it converts the conversation from "cheap relative to history" to "what would have to happen for today's price to make sense?"

### 1.5 Research Roadmap

The thesis proceeds in the same order that a working investor should.

First, it establishes why reverse DCF is conceptually suited to emerging-market value investing and why Damodaran's treatment of country risk, discount rates, and storytelling matters for Thai markets.

Second, it presents the methodological architecture. That section is intentionally explicit because a backtest without a clear data-timing rule is just an elegant form of hindsight.

Third, it clarifies the data reality of the repository. The work began as a broader Thai reverse DCF exploration and evolved into a stricter thesis-ready pipeline. The thesis refuses to hide that evolution.

Fourth, it reports results with the correct hierarchy of evidence.

Fifth, it discusses what the results mean economically and where the framework is likely to break.

That is also how valuation should be practiced. Build the logic, inspect the data, test the claim, and then decide how much confidence the evidence deserves.

## 2. Literature Review: Damodaran's DCF Principles and Their Emerging-Market Application

### 2.1 The DCF Framework

At its core, DCF valuation is built on a straightforward identity: the value of an asset is the present value of its expected cash flows, discounted at a rate that reflects the risk of those cash flows. That framework is theoretically elegant, but operationally fragile. Every DCF model contains embedded assumptions about growth, margins, reinvestment, leverage, and the discount rate. The model's usefulness therefore depends less on mathematical complexity than on how honestly those assumptions are handled.

Damodaran's work has long emphasized that valuation is not an exercise in spreadsheet engineering. It is a narrative-to-number discipline. The analyst begins with a story about the business, converts that story into cash-flow and growth assumptions, and then asks whether the market price reflects a better or worse story. The real valuation question is never "what is the precise value?" It is "what set of assumptions is required to justify today's price, and do I believe those assumptions?"

That framing naturally leads to reverse DCF.

### 2.2 Reverse DCF as an Expectations Framework

Reverse DCF begins where conventional DCF ends. Instead of assuming growth and solving for value, it assumes price and solves for the growth expectation embedded in price. This inversion has two advantages.

First, it exposes the market narrative. If a stock trades at a price that implies a high growth rate, the investor knows immediately that it is not enough for the company to be merely "good"; it has to be good enough to justify that embedded optimism. If a stock trades at a price implying low or negative growth, the investor can ask whether the pessimism is excessive.

Second, it reduces the temptation to smuggle preferences into valuation. Analysts often choose inputs that rationalize a pre-existing view. Reverse DCF is harder to abuse in that way because the key output is the market's implied expectation, not the analyst's preferred intrinsic value.

For value investing, this matters. Value is not just about low multiples. It is about a mismatch between what price implies and what business performance can plausibly deliver. Reverse DCF is therefore well-suited to a market such as Thailand, where sector structures differ sharply and the same accounting ratio can imply very different stories.

### 2.3 Country Risk, Discount Rates, and Emerging Markets

One of Damodaran's enduring contributions is to insist that emerging-market valuation must incorporate country risk explicitly. The risk-free rate, equity risk premium, beta, and cost of debt do not exist in a vacuum. An emerging-market firm's cost of equity is shaped not only by its sector and leverage, but also by the risk characteristics of the country in which it operates.

The local note in `docs/damodaran-stern-datasets-thai-set.md` extracts two Thailand ERP values from the April 1, 2026 country risk premium file:

- 5.8748% using the CDS-based route
- 7.1039% using the rating-based route

Those numbers should not be read as a binary choice between right and wrong. They define a range of plausible country-risk assumptions. The CDS-based route is more market-linked and faster moving. The rating-based route is more conservative and slower moving. For live valuation, that range is useful. For historical backtests, however, importing a 2026 ERP into prior ranking dates would contaminate the test with hindsight. That is why this thesis distinguishes between live valuation context and historical backtest safety.

### 2.4 Bottom-Up Beta and Industry Structure

Another Damodaran principle relevant here is the use of bottom-up betas. Direct regression betas for Thai stocks can be noisy, especially for thinner names or shorter histories. Industry betas, unlevered and then relevered using firm-specific capital structure, are often more informative. The local repository note on emerging-market betas and WACC benchmarks uses Damodaran's January 5, 2026 files to map common Thai sectors to industry proxies such as regional banks, telecom services, real estate development, hospitals, integrated oil and gas, food processing, and utilities.

This matters for two reasons. First, it provides a way to sanity-check discount rates. Second, it underscores that Thai sectors should not be treated as homogeneous. A hospital and a coal producer may both look inexpensive on a multiple screen, but their risk architecture is entirely different.

### 2.5 The Skepticism Principle

The most important lesson from Damodaran's broader body of work is methodological rather than computational: be skeptical of precision, especially when data quality is limited. In practical terms, that implies several choices that shape this thesis.

- Use simple, interpretable ranking rules before adding complexity.
- Separate valuation context from backtest-safe assumptions.
- Treat results as conditional on data quality, not as universal proof.
- Report exclusions and missingness explicitly.
- Avoid tuning a model until it flatters the hypothesis.

That skepticism is especially important in this repository because the data architecture evolved over time. Early artifacts were built for exploration. Later artifacts were built for thesis-grade evidence. A serious literature-informed methodology has to preserve that distinction.

### 2.6 Reverse DCF and Value Investing in the Thai Context

Thai value investing is often described in terms of low P/E, high dividend yield, price-to-book discounts, or property and bank cycles. Those tools can be useful, but they are incomplete. Low multiples often signal real business problems, and high dividend yields can simply reflect absent growth. Reverse DCF improves the conversation by reframing the question. Instead of asking whether a stock looks cheap, it asks what growth the market is assuming, whether that assumption is credible, and whether the investor has an information or interpretation edge.

That is why reverse DCF belongs in a Thai value investing framework. It does not replace qualitative judgment. It disciplines it.

### 2.7 Point-in-Time Data, Survivorship, and the Literature of Honest Backtesting

There is another strand of literature that matters here even if it is less glamorous than valuation theory: the literature of research design. Many quantitative value strategies fail not because the intuition is wrong, but because the test is contaminated. If the analyst uses information that was not actually available at the decision date, the strategy will look smarter in history than it could ever be in live investing. If the analyst ignores delisted firms, the surviving universe will look healthier than the market that investors actually faced. If the analyst tunes parameters until the curve looks beautiful, the strategy becomes a machine for describing the past rather than investing in the future.

This thesis treats those concerns as central rather than peripheral. That is why the repository's later-stage artifacts are so important. A dated observation with a statement date, availability date, and reporting lag is not just a data-management detail. It is a research ethics device. An exclusion file is not just a debug aid. It is a reminder that a strategy operates on the market it can score, not on the market we wish it had scored.

That perspective also changes how one should read positive results. A high CAGR in a simplified simulation is interesting. A more modest active return in a stricter benchmark-relative backtest may be more valuable because it is more believable. The history of factor research is full of strategies that looked extraordinary until implementation details were handled honestly. The right standard for this thesis is therefore not maximum performance. It is maximum defensibility subject to the data constraints of the project.

### 2.8 The Story-Numbers Loop

A final conceptual point from Damodaran's broader approach deserves emphasis. In good valuation, narrative and numbers constantly interrogate each other. If the story says a Thai telecom is mature and defensive, the implied growth requirement should be modest and the discount rate should reflect that business model. If the story says a property developer is deeply cyclical and heavily balance-sheet-driven, the analyst should be skeptical of a low multiple that looks optically cheap. If the story says a bank is well-capitalized but the market is pricing it for prolonged earnings stagnation, the reverse DCF output becomes a statement about what the market fears.

That loop is the heart of this thesis. Reverse DCF does not remove judgment. It tells the investor where judgment is required.

## 3. Methodology: A Reverse DCF Framework for Thai SET Markets

### 3.1 Research Design

The methodology in this thesis is deliberately layered. The repository contains both exploratory and audited evidence, and the thesis should use both without confusing them.

The evidence hierarchy is as follows:

| Evidence layer | Main artifact | What it measures | Strength | Limitation |
| --- | --- | --- | --- | --- |
| Exploratory broad-study simulation | `backtest_results/metrics_20260411_133531.txt` and `portfolio_20260411_133531.csv` | Cross-sectional reverse DCF ranking quality and simulated portfolio outcomes | Broad cross-section, practical intuition | Not point-in-time audited; should not be treated as a full historical backtest |
| Audited thesis bundle | `research_data/latest/backtest/*` and `research_data/latest/thesis_bundle/*` | Quarterly portfolio formation from dated observations, benchmark-relative forward returns, and explicit no-lookahead checks | Stronger thesis evidence | Narrower investable universe; free-data constraints remain |

This hierarchy is not a weakness. It is a strength. It allows the thesis to say, honestly, that the framework first looked promising in a broader exploratory lane and then retained positive evidence under a stricter and more defensible design.

### 3.2 Data Inputs

The audited workflow uses the generated research bundle in `research_data/latest/`, with the following core inputs:

- `fundamentals_snapshot.csv`
- `fundamental_observations.csv`
- `price_history.csv`
- `benchmark_history.csv`
- `fundamental_coverage.csv`
- `price_coverage.csv`
- `reverse_dcf_exclusions.csv`

The exploratory lane also relies on processed snapshots under `data/processed/` and saved simulation outputs under `backtest_results/`.

### 3.3 Observation Dating and No-Lookahead Logic

The central methodological issue in any backtest based on fundamentals is timing. Financial statements are not available to investors on the statement date. They are available only after a reporting lag. This thesis handles that issue by attaching both `Statement_Date` and `Availability_Date` to each observation. At each rebalance date, the latest eligible observation is the latest row satisfying:

`Availability_Date <= Rebalance_Date`

This rule is simple, transparent, and more defensible than using the latest available data retroactively. It does not eliminate every timing concern, but it removes the most obvious form of lookahead leakage.

The latest audit artifact in `research_data/latest/backtest/no_lookahead_audit.md` reports:

- WACC mode: fixed
- no-lookahead failures: 0

That does not prove the research design is perfect. It proves that the implemented timing rule is internally consistent in the audited sample.

### 3.4 Reverse DCF Signal Construction

For each eligible stock at each rebalance date, the workflow uses the latest available dated values for free cash flow, net debt, shares, and historical revenue growth. It then uses market price to back out an implied growth assumption. The ranking logic compares what the market appears to require with what the business has actually delivered.

In the current audited implementation, the core signal is:

`Signal Score = Actual Revenue Growth - Implied Growth Rate`

The intuition is straightforward.

- A higher score implies that the firm's observed business growth is stronger relative to what the market price implies.
- A lower or negative score implies that market expectations are already rich relative to observed operating reality.

This is not a claim that historical revenue growth will persist unchanged. It is a disciplined way to compare realized business momentum with embedded market expectations.

### 3.5 Discount Rate Policy

For live Thai valuation, the most intellectually satisfying approach would be to let discount rates vary with country risk, sector risk, leverage, and possibly macro regime. For historical backtests, that creates a danger: if discount-rate inputs are taken from the latest snapshot and then applied backward in time, the backtest leaks hindsight.

The thesis therefore adopts a two-part policy.

1. For historical ranking and backtesting, use a fixed-WACC framework.
2. For interpretation and robustness, use Thailand ERP and industry WACC data as external anchors and sensitivity references.

This is why the backtest manifest records `wacc_mode = fixed`, while the thesis discussion still references Thailand ERP values and Damodaran's industry files. It is a compromise between realism and backtest integrity, and in this context it is the right compromise.

### 3.6 Portfolio Construction

The audited backtest uses the following design:

- Rebalance frequency: quarterly
- Portfolio rule: equal-weight top 10 stocks by signal score
- Benchmark: `^SET.BK`
- Holding periods tested: 3, 6, and 12 months
- Historical scoring assumption: fixed WACC

The exploratory simulation path differs. It produces a top-20 equal-weight portfolio from a broader processed universe and reports simulated 3-year outcomes. That path is useful as an exploratory cross-sectional screen but is not treated here as equivalent to the audited backtest.

### 3.7 Exclusions and Transparency

An important feature of the methodology is that exclusions are reported, not hidden. In the audited backtest, 242 exclusion rows are recorded. The main reasons are:

- `invalid_fcf` (199)
- `no_convergence` (22)
- `no_price_on_or_before` (11)
- `no_available_observation` (7)
- `invalid_shares` (3)

This matters because a backtest can look better simply by ignoring the names it cannot score. By writing exclusions to disk, the repository makes the universe shrinkage visible.

The broader set-level filters are also explicit. In `research_data/set100_working/reverse_dcf_exclusions.csv`, 85 names pass the basic reverse DCF filter and 15 are excluded for missing or non-positive free cash flow. In `research_data/latest/reverse_dcf_exclusions.csv`, 45 of 50 names pass the input filter. These are not merely technical details. They tell the reader how much of the market the framework can actually touch.

### 3.8 Hypotheses

The thesis tests three hypotheses.

1. A reverse DCF ranking strategy can produce positive active returns against the SET benchmark on average.
2. The strongest effects should appear in shorter to medium horizons, where expectations gaps can normalize faster than full business fundamentals.
3. The framework's usefulness will vary materially across sectors because the meaning of a growth shortfall or growth surprise is not uniform across the Thai market.

### 3.9 Research Philosophy

The philosophy of the methodology is worth stating plainly.

- The goal is not to prove that reverse DCF always works.
- The goal is not to optimize parameters until the result is flattering.
- The goal is to create a transparent, investable, country-risk-aware framework that can survive honest scrutiny.

That is a better standard for value investing research than producing a beautiful backtest that no serious investor should trust.

### 3.10 Formal Valuation and Portfolio Equations

For completeness, the framework can be written in standard valuation notation.

The conventional DCF identity is:

`Value = sum(FCF_t / (1 + WACC)^t) + Terminal Value / (1 + WACC)^n`

with:

`Terminal Value = FCF_n * (1 + g) / (WACC - g)`

In a reverse DCF setup, price is observed and growth is the unknown:

`Market Value = f(g | FCF, WACC, shares, debt, cash, horizon assumptions)`

The solver searches for the growth rate `g*` such that:

`Estimated Equity Value per Share(g*) = Observed Market Price`

In the audited repository workflow, the practical ranking signal does not stop at the implied growth estimate. It compares implied growth to observed operating history:

`Signal Score = Actual Revenue Growth - Implied Growth Rate`

Portfolio construction is then:

`Select top N stocks by Signal Score`

`Weight_i = 1/N`

Benchmark-relative performance for horizon `h` is:

`Active Return_h = Portfolio Return_h - Benchmark Return_h`

The hit rate is:

`Hit Rate_h = Number of rebalances with Active Return_h > 0 / Total rebalances`

Writing the methodology this way makes an important point. The framework has moving parts, but it is not mathematically exotic. Its usefulness depends less on clever formulas than on whether the inputs are dated correctly and whether the implied expectations are economically interpretable.

### 3.11 Step-by-Step Research Algorithm

To make the workflow operational rather than abstract, the audited research process can be described as an algorithm.

1. Define the Thai stock universe available from the free-data pipeline.
2. Pull historical price series for each stock and the benchmark.
3. Pull annual and quarterly statement observations and assign statement dates.
4. Impose a reporting lag to derive availability dates.
5. At each rebalance date, filter each stock's observations to those available on or before the rebalance date.
6. Use the latest eligible observation to compute the reverse DCF implied growth rate.
7. Compute the signal score as actual revenue growth minus implied growth.
8. Rank all eligible names by signal score.
9. Form an equal-weight top-N portfolio.
10. Measure forward stock and benchmark returns over 3, 6, and 12 months.
11. Record exclusions, universe counts, turnover, and active returns.
12. Run no-lookahead and sensitivity diagnostics.
13. Export all artifacts into a thesis-readable bundle.

This algorithm matters because it is falsifiable. At each step, a reviewer can ask whether the repository does what it claims. That is what separates a thesis workflow from a loose investment memo.

### 3.12 Why Equal Weight and Top-N Were Chosen

The portfolio construction is intentionally simple. Equal weighting and a top-10 selection rule are not meant to be the theoretically optimal implementation. They are meant to reduce degrees of freedom.

A cap-weighted portfolio would allow the largest Thai companies to dominate the signal, making it harder to know whether the framework is adding value or merely leaning on benchmark structure. A heavily optimized risk model would create opportunities for overfitting. A very small portfolio would produce concentration that might flatter or punish the signal by chance. A very large portfolio would dilute the cross-sectional effect.

Top-10 equal weight is therefore a pragmatic middle ground. It gives the signal enough room to matter while keeping the construction transparent.

### 3.13 Why the Framework Uses Revenue Growth as the Realized Comparator

One may reasonably ask why the realized comparator is revenue growth rather than earnings growth, free cash flow growth, or return on capital. The answer is partly practical and partly conceptual.

Revenue growth is imperfect, but it is broadly observable, less sensitive than earnings to one-off accounting items, and easier to compare across sectors than free cash flow in many cases. In a reverse DCF context, the goal is not to forecast the full business model with precision. It is to compare price-implied expectations with a clean summary of realized operating trajectory.

That said, future research should test alternative realized comparators. Earnings growth, normalized free cash flow growth, and return-on-capital persistence may all alter the signal's effectiveness by sector.

## 4. Data and Coverage: The Thai SET Universe in This Repository

### 4.1 What the Repository Actually Contains

One of the first duties of a thesis is to state the sample honestly. The assignment brief references 88 Thai stocks and 20 quarters of fundamentals. The repository, as checked on April 11, 2026, shows a more nuanced picture.

The current files support three related but distinct universes.

| Dataset lane | File root | Tickers | Observations | Notes |
| --- | --- | ---: | ---: | --- |
| Broad processed snapshot | `data/processed/fundamentals/quarterly/fundamentals.csv` | 100 | 100 rows | Latest cross-sectional snapshot, not a dated panel |
| Working historical bundle | `research_data/set100_working/` | 100 | 1,081 dated observations | Annual and quarterly statement observations; mean 10.81 observations per ticker |
| Audited thesis bundle | `research_data/latest/` | 50 | 536 dated observations | Current point-in-time audited research bundle used for benchmark-relative backtest |

That distinction matters. The broad study is valuable because it covers more names. The audited study is valuable because it is more defensible. A serious reader should prefer the stricter evidence when the two differ.

### 4.2 Broad Cross-Sectional Universe

The processed broad snapshot covers 100 Thai equities. Sector representation is diversified:

| Sector | Stocks in processed universe |
| --- | ---: |
| Financial Services | 18 |
| Consumer Cyclical | 14 |
| Industrials | 14 |
| Real Estate | 12 |
| Consumer Defensive | 11 |
| Energy | 7 |
| Utilities | 7 |
| Healthcare | 6 |
| Communication Services | 5 |
| Basic Materials | 3 |
| Technology | 3 |

Once basic validity constraints are applied, 83 names remain with positive market capitalization and positive EPS, and 82 names remain signal-eligible under the simplified reverse DCF simulation logic. That is close enough to the "roughly high-80s" framing in the earlier scripts to see where the brief came from, but the repository state should be treated as the source of record.

Within that valid-signal subset, financial services remains the largest group, followed by industrials and consumer cyclicals. That is useful context. If a reverse DCF framework works in Thailand, part of what it is doing will almost certainly reflect how the market prices banks, lenders, and property-linked businesses relative to observed fundamentals.

### 4.3 Historical Working Bundle

The broader dated bundle under `research_data/set100_working/` contains 1,081 annual and quarterly observations across 100 tickers.

- Mean observations per ticker: 10.81
- Median observations per ticker: 11
- Minimum observations per ticker: 8
- Maximum observations per ticker: 12
- Quarterly rows: 589
- Annual rows: 492
- Statement-date range: September 30, 2021 to January 31, 2026

This is not a 20-quarter panel. It is a shorter but still useful dated history. The implication is important: the research has enough depth to support quarterly rebalancing across several years, but not enough to claim a long-cycle multi-decade test. Any conclusions must be scaled to that reality.

### 4.4 Audited Thesis Bundle

The audited thesis bundle is narrower. It contains:

- 50 tickers
- 536 dated observations
- 292 quarterly rows
- 244 annual rows
- statement-date range from September 30, 2021 to December 31, 2025

Its sector composition is as follows:

| Sector | Stocks in audited bundle |
| --- | ---: |
| Financial Services | 12 |
| Consumer Cyclical | 7 |
| Industrials | 7 |
| Utilities | 6 |
| Consumer Defensive | 5 |
| Energy | 4 |
| Communication Services | 2 |
| Healthcare | 2 |
| Real Estate | 2 |
| Technology | 2 |
| Basic Materials | 1 |

The shrinkage from 100 names to 50 is not arbitrary. It reflects the free-data workflow, the desire for cleaner dated observations, and the stricter pipeline used for the backtest. That narrower universe is a limitation, but it is also why the audited evidence carries more weight.

### 4.5 Coverage and Exclusion Diagnostics

The repository's coverage diagnostics reveal an important truth about free-data investing research: availability shapes investability.

At the input-filter stage:

- 85 of 100 names pass the reverse DCF filter in the `set100_working` bundle.
- 45 of 50 names pass the reverse DCF filter in the audited `latest` bundle.

At the audited backtest stage:

- 408 signals are generated
- 39 portfolio rows are recorded
- 242 exclusion rows are recorded
- average universe count is 50
- average excluded count is 18.62

This tells a clear story. The strategy is not operating on a frictionless universe. It is operating on the subset of the Thai market for which dated fundamentals, usable prices, valid share counts, and convergent reverse DCF solutions are available. That does not invalidate the framework. It defines the boundary of what the framework currently knows how to value.

### 4.6 Portfolio Characteristics in the Exploratory Lane

The top-20 portfolio saved in `backtest_results/portfolio_20260411_133531.csv` offers a useful look at the kinds of stocks the broad study tends to select.

- Portfolio size: 20 stocks
- Equal weight: 5% per stock
- Sector concentration: 8 financials, 3 consumer defensives, 3 industrials, 3 real estate names, and single names in basic materials, consumer cyclical, and energy
- Mean P/E: 6.75x
- Mean P/B: 0.67x
- Mean ROE: 11.54%

In other words, the simplified broad-study portfolio does not look like a speculative lottery ticket. It looks like a classic value portfolio: low multiples, acceptable profitability, and a large presence of financials and asset-heavy sectors.

That is exactly the sort of "story behind the numbers" one should expect. A reverse DCF framework in Thailand is likely to surface firms where the market has compressed growth expectations in sectors exposed to macro, credit, or cyclical fear.

### 4.7 Data Provenance and Source Policy

The source policy is central to the credibility of the dataset.

The project uses Yahoo Finance through `yfinance` as the primary free data source. Official SET pages are retained only for optional validation. This choice was not made because Yahoo is perfect. It was made because a thesis-grade backtest requires historical completeness at tolerable cost, and in this repository that tradeoff favored Yahoo over more official but less accessible or less reusable sources.

The consequence is important. The pipeline is reproducible by an independent researcher, but it inherits the weaknesses of a free-source ecosystem:

- some fields may be missing or inconsistent,
- historical price coverage may differ across names,
- statement histories may be shorter than desired,
- edge-case corporate events may be handled imperfectly.

Rather than hiding those weaknesses, the repository writes manifests, quality files, coverage files, and validation references. That is exactly the right design. In emerging-market research, source realism matters more than the illusion of pristine data.

### 4.8 What the Sample Window Really Represents

The audited sample window from March 31, 2023 to March 31, 2026 should be thought of as a short but useful modern Thai market regime sample. It contains:

- negative benchmark outcomes over some shorter windows,
- uneven sector performance,
- enough quarterly rebalances to see repeated selection behavior,
- but not enough time to claim full-cycle permanence.

That last point is easy to forget when results are positive. A three-year audited window can reveal whether the framework is directionally promising. It cannot resolve whether the edge is structural, episodic, or partly accidental.

### 4.9 What the Dataset Says About Investability

The data files tell an economically meaningful story about investability. The average audited universe count is 50, but the average excluded count is 18.62. That means the strategy is effectively choosing from a materially narrower pool than the raw snapshot suggests. The gap between "stocks in the universe" and "stocks that can actually be scored and held under the methodology" is one of the most important hidden variables in empirical investing research.

From an implementation perspective, that is not just a limitation. It is a practical warning. A real investor using reverse DCF in Thailand should expect the screenable universe to fluctuate with data completeness, sector composition, and statement availability. The framework is not a static factory. It is a process operating under information constraints.

## 5. Results: Portfolio Characteristics and Performance

### 5.1 Broad-Study Simulation Results

The earliest headline result in the repository comes from `backtest_results/metrics_20260411_133531.txt`, which reports:

- CAGR: 15.6756%
- win rate: 93.1%
- median return: 54.78%
- expected return: 17.02%

Those are strong numbers. They are also dangerous if interpreted carelessly.

The correct way to read them is as outputs from a simplified simulation path that uses a broad cross-sectional reverse DCF ranking, a top-20 equal-weight portfolio, and simulated return paths anchored to Thai market return assumptions plus portfolio quality adjustments. They are useful because they tell us the cross-sectional signal is selecting a portfolio with economically attractive characteristics. They are not equivalent to a point-in-time historical backtest with dated observations and benchmark alignment.

This is not a technicality. It is the difference between exploratory evidence and thesis-grade evidence.

### 5.2 Audited Benchmark-Relative Backtest Results

The stronger result set comes from `research_data/latest/backtest/report.md` and `summary.csv`. The portfolio is rebalanced quarterly, holds the top 10 names by signal score, and is compared with `^SET.BK`. The results are:

| Horizon | Portfolio Return | Benchmark Return | Active Return | Hit Rate |
| --- | ---: | ---: | ---: | ---: |
| 3 months | 1.6785% | -0.0034% | 1.6818% | 53.85% |
| 6 months | 2.2032% | 0.5519% | 1.6514% | 69.23% |
| 12 months | 2.4290% | 1.5788% | 0.8502% | 61.54% |

The result is attractive for three reasons.

First, active return is positive in every tested horizon. That matters more than the raw return levels because the Thai market environment across the sample was not uniformly benign.

Second, the highest hit rate appears at 6 months, while the highest average active return appears at 3 months. That pattern is plausible. Expectations gaps often close faster than full business fundamentals normalize, especially in markets where repricing can be abrupt.

Third, the audited design reports zero no-lookahead failures. That does not make the result immune to criticism, but it raises the credibility bar substantially above a pure snapshot-based screen.

### 5.3 Magnitude Versus Credibility

An investor reading the thesis may be tempted to ask which result should matter more: the larger 15.68% CAGR from the broad simulation or the more modest but cleaner active-return figures from the audited bundle. The right answer is that credibility matters more than magnitude.

If the broad simulation had looked weak and the audited bundle had looked strong, the stricter result would still deserve more weight. The same principle applies here. The exploratory result is encouraging because it suggests the signal is economically meaningful. The audited result is persuasive because it survives a more defensible research design.

### 5.4 Sector Results

Sector behavior in the appendix is uneven, and that is exactly what one should expect in a valuation strategy.

From `research_data/latest/backtest/appendix.md`:

- Technology generated the strongest mean active return across all three horizons.
- Communication services remained positive across all horizons.
- Financial services had the largest number of selections and remained positive on average.
- Industrials and basic materials were materially weaker.

This tells an important story. Reverse DCF works best where market expectations diverge from operating reality in a way that is economically meaningful and not instantly arbitraged away. Technology and communication names can reprice sharply when the market is too skeptical. Financials can remain attractive when capital and credit fears depress expectations more than actual earnings power justifies. Industrials and basic materials, by contrast, are more exposed to cyclical or balance-sheet uncertainty that can make "cheap" valuations deserved.

### 5.5 WACC Sensitivity

The appendix also reports fixed-WACC sensitivity at 6%, 8%, and 10%.

| WACC | 3M Active Return | 6M Active Return | 12M Active Return |
| --- | ---: | ---: | ---: |
| 6% | 1.8287% | 1.5521% | 0.6263% |
| 8% | 1.6818% | 1.6514% | 0.8502% |
| 10% | 1.8245% | 1.8913% | 1.3786% |

The key takeaway is not that a higher WACC is "better." It is that the positive result is not confined to one narrow fixed-WACC assumption. That reduces the risk that the strategy's apparent success is nothing more than parameter accident.

### 5.6 What the Results Mean

The correct thesis-level conclusion is modest but positive:

In the audited implementation, reverse DCF appears to help identify Thai equities whose market-implied expectations are lower than their observed business strength, and those names, on average, outperform the SET benchmark over tested holding periods.

That is a defensible claim. The stronger claim, that reverse DCF is proven to beat the Thai market in a broad and durable sense, is not defensible on the current evidence.

### 5.7 Reading the Horizon Pattern Carefully

The horizon pattern deserves a more detailed reading because it reveals something about how value may work in Thai markets.

The 3-month horizon shows the highest average active return. That suggests the signal is capturing a repricing effect. The market may be responding to the realization that it priced some firms with too much pessimism. A quick rerating is consistent with value gaps that close once near-term business evidence becomes harder to ignore.

The 6-month horizon shows the highest hit rate. That suggests the signal is not only producing occasional bursts of outperformance, but doing so with greater consistency over a medium horizon. For investors, that may be the most attractive balance between patience and confirmation.

The 12-month horizon remains positive, but the active-return spread is smaller. There are two plausible interpretations. One is that the valuation gap closes early and then the benchmark catches up. The other is that longer horizons expose the signal to more macro, sector, and fundamental noise unrelated to the original expectations gap. Either way, the pattern supports a practical conclusion: reverse DCF in this implementation looks more like a medium-term re-rating framework than a buy-and-forget compounding machine.

### 5.8 Why the Broad Portfolio's Characteristics Matter

The broad-study portfolio's low average P/E and low average P/B, combined with acceptable average ROE, are not incidental facts. They provide a bridge between traditional value investing and the reverse DCF framework.

Traditional value investors are often most comfortable when a strategy selects businesses that look cheap on multiple dimensions and still generate respectable returns on equity. The broad-study portfolio does exactly that. In effect, the reverse DCF signal is not fighting classic value intuition. It is refining it. The framework appears to surface stocks where conventional cheapness coincides with a market-implied growth bar that is not especially demanding.

That is important because a reverse DCF strategy that constantly selected high-multiple glamour names on the theory that expectations were still "reasonable" would be much harder to reconcile with value investing. The portfolio characteristics here tell a more grounded story.

### 5.9 Selection Breadth and Concentration

The broad-study portfolio is dominated by financials and asset-heavy sectors, while the audited appendix still shows material influence from financial services. This raises two simultaneous interpretations.

The optimistic reading is that the Thai market may systematically over-discount sectors where leverage, macro sensitivity, and balance-sheet complexity frighten investors more than realized business performance justifies.

The skeptical reading is that part of the signal's effect may simply be a disguised sector bet. That is why future research should include sector-neutral ranking or sector-controlled portfolio formation. The current results are positive, but they do not yet prove that the framework's edge is fully stock-specific rather than partly sector-structural.

## 6. Discussion: Sector Structure, Market Regimes, and the Story Behind the Numbers

The most useful way to interpret the results is through the story they tell about Thai markets.

Reverse DCF is not selecting stocks simply because they are cheap on static ratios. It is selecting stocks where the gap between price-implied expectations and realized operating performance appears favorable. In practice, that means the strategy will tend to work best in three kinds of situations.

First, where the market has become too pessimistic about otherwise viable businesses. This is common in financials, property-linked names, and cyclical sectors where macro fear overwhelms business-level evidence.

Second, where high-quality firms are temporarily priced as though growth is structurally impaired. Technology and communication names in the appendix fit that pattern better than deep cyclicals.

Third, where a company's business quality remains acceptable but the market has compressed the multiple to levels that assume little or no future growth. That is classic value investing territory.

### 6.1 Why Shorter Horizons Look Better

The stronger 3- and 6-month active returns relative to the 12-month figure are plausible. Value gaps in emerging markets often close in bursts rather than in smooth multi-year progressions. When the market narrative changes, prices can move faster than fundamentals. A stock that is priced for near-stagnation can rerate quickly once the market realizes the business is not deteriorating as fast as feared.

That is why the 6-month horizon's high hit rate matters. It suggests that the expectations gap may be monetized within a medium-term investment window without requiring the investor to wait indefinitely for a perfect fundamental convergence story.

### 6.2 Why Sector Dispersion Is a Feature, Not a Bug

Many investors want a strategy that works everywhere. That is the wrong expectation here. Reverse DCF is strongest where cash flows, growth expectations, and discount-rate assumptions can be compared in a meaningful way. It is weaker where cash flow is noisy, accounting is a poor proxy for economics, or sector narratives are dominated by variables the model does not capture well.

Banks are a special case. Free cash flow is conceptually awkward in financials, and balance-sheet structure is part of the business model rather than just financing. Yet Thai financials still appear prominently in both the broad-study portfolio and the audited appendix. That suggests the framework may be capturing value through earnings quality, profitability, and suppressed growth expectations rather than through a textbook industrial-company DCF logic alone. The implication for future research is not to avoid financials, but to treat them with model-specific care.

### 6.3 Country Risk and Time-Varying Parameters

One of the tensions in the thesis is between live realism and historical integrity. In real valuation, discount rates should vary with country risk, business risk, and financing conditions. In historical testing, letting those parameters float using latest-available data can quietly introduce hindsight bias.

The fixed-WACC design chosen here solves one problem and creates another. It avoids the most obvious lookahead problem, but it also compresses real cross-sectional and temporal variation in discount rates. That is acceptable for a baseline test. It is not the last word. The real lesson is that time-varying parameters matter, but they must be implemented in a way that does not cheat.

This is where Damodaran's framework is useful conceptually. It reminds the analyst that valuation is local, risk is not constant, and a mature-market discount rate should not be smuggled into an emerging-market analysis simply because it makes the spreadsheet cleaner.

### 6.4 Overfitting and the Discipline of Humility

A positive backtest is not a victory lap. It is an invitation to ask harder questions.

- Would the result survive a longer historical window?
- Would it survive a more complete universe including delisted names?
- Would it survive sector-neutral construction?
- Would it survive alternative definitions of realized growth?
- Would it survive a bank-specific or property-specific variant of the model?

The best feature of this repository is that it has begun to ask those questions rather than suppress them. The presence of audit artifacts, exclusion logs, sector summaries, and WACC sensitivity tables is a sign of methodological maturity. In valuation research, humility is not a weakness. It is part of the craft.

### 6.5 Practical Implications for Thai Investors

The framework has practical value precisely because it is simple enough to be used.

An investor can apply it in four steps.

1. Estimate what growth the current price is implicitly demanding.
2. Compare that implied growth with observed operating reality and qualitative business prospects.
3. Anchor discount rates in Thai country risk and sector structure, but keep historical testing clean.
4. Demand a margin of safety, especially in sectors where cash flow is cyclical or accounting quality is noisy.

That is a coherent value investing process. It does not promise certainty. It imposes discipline.

### 6.6 What a Thai Investor Should Do With a Reverse DCF Output

A reverse DCF output should not trigger an automatic buy or sell. It should trigger a checklist.

If implied growth is much lower than observed operating reality, the investor should ask:

- Is the market correctly pricing a structural decline that historical data has not yet captured?
- Is leverage too high for the business quality to matter?
- Is the company in a sector where free cash flow is misleading?
- Is there a governance, liquidity, or capital-allocation risk that the model cannot see?

If the answer to those questions is mostly no, the stock may be a legitimate opportunity.

If implied growth is much higher than operating reality, the investor should ask:

- Is the market extrapolating a cyclical high?
- Is margin structure likely to normalize downward?
- Is the multiple simply reflecting a quality premium that the business deserves?

In other words, the reverse DCF result is not the decision. It is the framing device that makes a better decision possible.

### 6.7 Reverse DCF as a Teaching Tool

One underappreciated benefit of reverse DCF is pedagogical. It trains investors to think like skeptics. Instead of asking, "What value do I get if I assume 8% growth?", they ask, "What growth is already embedded in this price, and do I buy that story?" That is a healthier way to think, especially in emerging markets where confidence can outrun evidence very quickly.

For Thai markets, that discipline may be particularly helpful for individual investors who are accustomed to narrative-heavy investing. Reverse DCF forces the narrative to carry a numerical burden.

### 6.8 Why the Framework Still Belongs to Value Investing

Some investors might argue that reverse DCF is simply another growth-expectations framework and therefore not obviously "value." That would be too narrow a definition of value investing. Value investing is not the worship of low multiples. It is the purchase of assets for less than they are worth, with a margin of safety. A framework that reveals when the market is demanding implausibly low or high growth is entirely consistent with that tradition.

In fact, reverse DCF may be more faithful to the spirit of value investing than a blind low-multiple screen because it forces the investor to confront what the market believes. True value investing has always involved taking issue with market expectations, not merely shopping for statistically cheap stocks.

## 7. Limitations and Risks

This thesis has several important limitations, and they should be stated directly.

### 7.1 Free-Data Constraints

The entire pipeline is built on free data, primarily via Yahoo Finance and `yfinance`, with official SET pages used only as optional validation references. That choice improves reproducibility and cost accessibility, but it creates coverage limits.

- The audited bundle contains only 50 names.
- Some stocks are excluded for missing or invalid free cash flow, missing dated observations, missing prices, or failed convergence.
- Historical depth is closer to 8 to 12 observations per ticker than to a long multi-cycle panel.

In other words, the framework is being tested on the market that free data can see, not necessarily the full market an institutional database would reveal.

### 7.2 Survivorship Bias

The repository does not yet implement a fully date-versioned Thai universe including delisted names through time. That means survivorship bias remains a live concern. If weaker firms disappear from the sample, the apparent attractiveness of the strategy may be overstated.

This matters especially in emerging markets, where corporate churn, restructuring, relisting, and data disappearance can distort history.

### 7.3 Fixed WACC Simplification

The use of a fixed WACC in the historical backtest is deliberate and defensible, but it is still a simplification. Different sectors in Thailand should not, in reality, have the same hurdle rate, and country risk itself is not constant through time. The current design therefore favors backtest integrity over economic granularity. That is acceptable for a baseline, but future extensions should move toward dated, sector-aware discount-rate frameworks without reintroducing lookahead bias.

### 7.4 Reverse DCF Is Only as Good as the Cash Flow Proxy

Reverse DCF works best for firms where free cash flow is a meaningful summary of business economics. It is less clean for banks, insurers, turnaround stories, and highly cyclical firms. Using a single framework across all sectors can therefore create hidden distortions.

The right response is not to abandon the framework. It is to segment it. Different sectors may need different implementations of "cash flow reality."

### 7.5 Short Audited Sample Window

The audited backtest runs from March 31, 2023 to March 31, 2026 across 13 rebalance dates. That is enough to generate evidence, but not enough to settle the question for all Thai market regimes. A strategy can look attractive over a three-year period and still fail over a full credit cycle, commodity cycle, or property downturn.

### 7.6 Overlapping Holding Windows

Testing 3-, 6-, and 12-month returns with quarterly rebalancing means some holding windows overlap. That is common in practical backtesting, but it reduces the independence of observations. The hit rates and average returns are still informative, but they should not be treated as if each outcome were fully independent.

### 7.7 The Exploratory Simulation Must Not Be Overstated

The broad-study 15.68% CAGR and 93.1% win rate are encouraging, but they do not come from the stricter audited design. Presenting them as if they were equivalent would overstate the evidence. The correct academic posture is to treat them as exploratory support, not as the thesis's definitive proof.

### 7.8 Availability-Date Modeling Is Still an Assumption

Even a careful reporting-lag framework is still an assumption. The thesis uses statement date plus a reporting lag as a proxy for market availability. In practice, different firms release information at different times, markets may partially anticipate outcomes, and some operational evidence becomes visible before official statements are published. The availability-date rule is therefore an improvement over naïve timing, not a perfect reconstruction of the information set investors had.

### 7.9 Benchmark Choice and Investable Frictions

The benchmark used is `^SET.BK`, which is reasonable for a broad Thai equity comparison. But benchmark choice is never neutral. A value strategy tilted toward smaller or sector-specific names might look different against sector benchmarks, equal-weight benchmarks, or investable ETF proxies. In addition, the audited results do not fully model all practical frictions such as capacity constraints, taxes, market impact, and the full range of trading costs. Those omissions matter more in thinner segments of the Thai market than they would in a very deep developed market.

### 7.10 Why These Limitations Do Not Nullify the Thesis

It is important not to overreact to limitations. A thesis does not need to be perfect to be useful. It needs to be honest about what it can establish.

This thesis can establish that:

- reverse DCF is conceptually well suited to Thai value investing,
- the repository contains positive audited benchmark-relative evidence,
- the framework's success varies by sector and horizon,
- and the evidence survives a nontrivial attempt to control lookahead bias.

It cannot establish that the framework will continue to outperform under all future Thai market conditions. That is a meaningful boundary, but not a fatal one.

## 8. Conclusion and Future Research

The central conclusion of this thesis is that reverse DCF is a useful value investing framework for Thai SET markets, but only when used with discipline.

Its usefulness lies in what it forces the investor to do. Instead of declaring a stock cheap because a ratio is low, the investor has to ask what growth and performance the market is pricing in. That is a better question. It converts valuation from a slogan into an expectations test. In Thai markets, where country risk, sector structure, leverage, and macro sensitivity matter, that expectations test is particularly valuable.

The empirical evidence in this repository is positive but layered.

- The broader exploratory study suggests the framework can produce a portfolio with classic value characteristics and strong simulated outcomes.
- The stricter audited bundle shows positive average active returns against the SET benchmark across 3-, 6-, and 12-month horizons, with zero no-lookahead failures in the latest audit.

Taken together, those results support a measured conclusion: reverse DCF deserves a place in the Thai value investor's toolkit.

But the framework is not complete. The next phase of research should focus on five extensions.

1. Build a date-versioned Thai universe including delisted and restructured names to address survivorship bias more directly.
2. Extend the historical depth of dated observations to cover more market regimes and stress periods.
3. Develop sector-specific reverse DCF variants, especially for financials, utilities, and highly cyclical firms.
4. Introduce dated, historically consistent country-risk and discount-rate term structures rather than a fixed-WACC baseline alone.
5. Test alternative portfolio constructions such as deciles, sector-neutral ranking, and capacity-aware weighting.

If those extensions continue to support positive active returns, the case for reverse DCF in Thai markets will become meaningfully stronger. If they weaken the result, that too will be useful knowledge. Good research is not about proving a framework right. It is about discovering the conditions under which it is useful.

### 8.1 Final Judgment

If one were forced to reduce the thesis to a single judgment, it would be this:

Reverse DCF is not a finished answer for Thai equities, but it is a better question.

It asks what the market is assuming, whether those assumptions are plausible, and whether price has moved too far from business reality. In a market where risk is local, stories matter, and cheapness is often ambiguous, that is exactly the kind of question a value investor should be asking.

## 9. References

### Academic and Market Framework References

1. Damodaran, Aswath. NYU Stern valuation datasets and country risk materials. Referenced locally through [docs/damodaran-stern-datasets-thai-set.md](/home/opc/RDCF/docs/damodaran-stern-datasets-thai-set.md).
2. Damodaran, Aswath. Country risk premium file `ctrypremApr26.xlsx`, referenced in the local note above.
3. Damodaran, Aswath. Emerging market beta and WACC files `betaemerg.xls` and `waccemerg.xls`, referenced in the local note above.

### Repository Methodology and Result References

4. [docs/thesis-methodology.md](/home/opc/RDCF/docs/thesis-methodology.md)
5. [docs/thesis-results.md](/home/opc/RDCF/docs/thesis-results.md)
6. [docs/executive-summary.md](/home/opc/RDCF/docs/executive-summary.md)
7. [research_data/latest/backtest/report.md](/home/opc/RDCF/research_data/latest/backtest/report.md)
8. [research_data/latest/backtest/appendix.md](/home/opc/RDCF/research_data/latest/backtest/appendix.md)
9. [research_data/latest/backtest/no_lookahead_audit.md](/home/opc/RDCF/research_data/latest/backtest/no_lookahead_audit.md)
10. [research_data/latest/backtest/manifest.json](/home/opc/RDCF/research_data/latest/backtest/manifest.json)
11. [research_data/latest/manifest.json](/home/opc/RDCF/research_data/latest/manifest.json)
12. [backtest_results/metrics_20260411_133531.txt](/home/opc/RDCF/backtest_results/metrics_20260411_133531.txt)
13. [backtest_results/portfolio_20260411_133531.csv](/home/opc/RDCF/backtest_results/portfolio_20260411_133531.csv)
14. [run_full_backtest.py](/home/opc/RDCF/run_full_backtest.py)
15. [run_simple_backtest.py](/home/opc/RDCF/run_simple_backtest.py)

## 10. Appendices

### Appendix A: Reproducibility Commands

Build the latest free-data bundle:

```bash
python -m rdcf.data_pipeline --output-dir research_data/latest --period 10y --sync-root-snapshot
```

Run the audited quarterly backtest:

```bash
python -m src.pipeline.backtest \
  --output-dir research_data/latest/backtest \
  --top-n 10 \
  --horizons 3 6 12 \
  --rebalance-frequency Q \
  --start-date 2020-01-01 \
  --wacc-mode fixed
```

Generate sector and WACC sensitivity outputs:

```bash
python -m src.pipeline.backtest_analysis \
  --output-dir research_data/latest/backtest \
  --wacc-values 0.06 0.08 0.10 \
  --top-n 10 \
  --horizons 3 6 12 \
  --rebalance-frequency Q \
  --start-date 2020-01-01
```

Generate thesis figures:

```bash
python -m src.pipeline.backtest_visuals --output-dir research_data/latest/backtest/figures
```

Bundle the thesis artifacts:

```bash
python -m src.pipeline.thesis_bundle --output-dir research_data/latest/thesis_bundle
```

### Appendix B: Key Empirical Facts Used in This Thesis

| Item | Value | Source |
| --- | --- | --- |
| Thailand ERP, CDS-based | 5.8748% | `docs/damodaran-stern-datasets-thai-set.md` |
| Thailand ERP, rating-based | 7.1039% | `docs/damodaran-stern-datasets-thai-set.md` |
| Broad processed universe | 100 stocks | `data/processed/fundamentals/quarterly/fundamentals.csv` |
| Broad valid positive-EPS universe | 83 stocks | local repository calculation |
| Broad signal-eligible universe | 82 stocks | local repository calculation |
| Working historical bundle | 100 tickers, 1,081 observations | `research_data/set100_working/fundamental_observations.csv` |
| Audited thesis bundle | 50 tickers, 536 observations | `research_data/latest/fundamental_observations.csv` |
| Audited no-lookahead failures | 0 | `research_data/latest/backtest/no_lookahead_audit.md` |
| Broad-study CAGR | 15.6756% | `backtest_results/metrics_20260411_133531.txt` |
| Broad-study win rate | 93.1% | `backtest_results/metrics_20260411_133531.txt` |
| Audited 3M active return | 1.6818% | `research_data/latest/backtest/report.md` |
| Audited 6M active return | 1.6514% | `research_data/latest/backtest/report.md` |
| Audited 12M active return | 0.8502% | `research_data/latest/backtest/report.md` |

### Appendix C: Thesis-Safe Interpretation Statement

The most defensible single-sentence conclusion from the repository is:

> In the current free-data implementation, a reverse DCF ranking strategy shows positive benchmark-relative evidence in Thai equities, especially over short and medium holding periods, but the result remains conditional on data coverage, explicit exclusions, and simplifying assumptions in discount-rate treatment.

That is the right tone for both an academic thesis and an investor who intends to stay honest.

### Appendix D: Sector Distribution Tables

#### D.1 Broad Processed Universe

| Sector | Count |
| --- | ---: |
| Financial Services | 18 |
| Consumer Cyclical | 14 |
| Industrials | 14 |
| Real Estate | 12 |
| Consumer Defensive | 11 |
| Energy | 7 |
| Utilities | 7 |
| Healthcare | 6 |
| Communication Services | 5 |
| Basic Materials | 3 |
| Technology | 3 |

#### D.2 Broad Valid-Signal Universe

| Sector | Count |
| --- | ---: |
| Financial Services | 18 |
| Industrials | 12 |
| Consumer Cyclical | 11 |
| Consumer Defensive | 10 |
| Real Estate | 7 |
| Healthcare | 6 |
| Utilities | 6 |
| Energy | 5 |
| Communication Services | 3 |
| Technology | 3 |
| Basic Materials | 1 |

#### D.3 Audited Thesis Bundle Universe

| Sector | Count |
| --- | ---: |
| Financial Services | 12 |
| Consumer Cyclical | 7 |
| Industrials | 7 |
| Utilities | 6 |
| Consumer Defensive | 5 |
| Energy | 4 |
| Communication Services | 2 |
| Healthcare | 2 |
| Real Estate | 2 |
| Technology | 2 |
| Basic Materials | 1 |

### Appendix E: Key Portfolio Characteristics

#### E.1 Broad-Study Top-20 Portfolio

| Metric | Value |
| --- | ---: |
| Portfolio size | 20 |
| Equal weight per stock | 5.0% |
| Mean ROE | 11.54% |
| Median ROE | 9.73% |
| Mean P/E | 6.75x |
| Median P/E | 7.18x |
| Mean P/B | 0.67x |
| Median P/B | 0.64x |

#### E.2 Broad Valid-Signal Universe

| Metric | Mean | Median |
| --- | ---: | ---: |
| ROE | 11.73% | 9.73% |
| P/E | 17.22x | 12.40x |
| P/B | 2.05x | 0.99x |

The contrast between the valid-signal universe and the actual selected portfolio shows that the reverse DCF ranking is tilting toward cheaper names without fully abandoning profitability. That is precisely the sort of mix a value investor would want to inspect further.

### Appendix F: Evidence Reconciliation Note

The repository contains multiple generations of artifacts. To avoid confusion, this thesis uses the following reconciliation rule:

1. When exploratory and audited artifacts disagree, prefer the audited artifact for thesis claims.
2. Use exploratory artifacts for intuition, cross-sectional characterization, and research history.
3. Never present the exploratory 15.68% CAGR and 93.1% win rate as equivalent to the audited quarterly benchmark-relative backtest.
4. Treat the 100-name working universe, the 85-name filter-passing universe, and the 50-name audited bundle as related but distinct samples.

This reconciliation note may seem procedural, but it is central to the integrity of the thesis. Research often evolves. The obligation is not to pretend that it did not evolve. The obligation is to explain what changed and why the final evidence hierarchy is credible.
