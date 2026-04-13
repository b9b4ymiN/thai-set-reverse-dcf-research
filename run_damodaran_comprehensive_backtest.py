#!/usr/bin/env python3
"""
Comprehensive Damodaran WACC Backtest Runner
=============================================
Runs 7 scenarios with progressively sophisticated WACC models based on the
Damodaran NYU Stern framework, then generates a comparison report for
academic analysis.

Each scenario tests a specific hypothesis about WACC construction for Thai SET stocks.
See Hypothesis Framework in .omc/plans/consensus-damodaran-wacc-backtest.md for details.

Scenarios:
  1. damodaran_cds     — Dynamic ERP (CDS-based, time-varying with 1-year lag)
  2. damodaran_rating  — Dynamic ERP (Rating-based, conservative)
  3. damodaran_size    — Size Premium adjusted WACC
  4. damodaran_beta    — Bottom-up Blended Beta (regression + fundamental)
  5. damodaran_full    — Full comprehensive (Rating ERP + Size Premium + Blended Beta)
  6. damodaran_full_cds— Full comprehensive (CDS ERP + Size Premium + Blended Beta)
  7. damodaran_roic    — Full comprehensive + ROIC Quality Screen (EVA: ROIC > WACC)

Output:
  research_data/source_of_truth_100/backtest_comprehensive/
  ├── damodaran_cds/       (per-scenario CSV outputs)
  ├── damodaran_rating/
  ├── damodaran_size/
  ├── damodaran_beta/
  ├── damodaran_full/
  ├── damodaran_full_cds/
  ├── damodaran_roic/
  ├── comparison_summary.csv
  └── comparison_report.md

Methodology references:
  - Damodaran, A. (2012). Investment Valuation, 3rd ed., Wiley. Ch.7-8, 12, 31.
  - Damodaran, A. (2006). Damodaran on Valuation, 2nd ed., Wiley. Ch.5, 9.
  - NYU Stern datasets: pages.stern.nyu.edu/~adamodar/New_Home_Page/datacurrent.html
"""

import sys
from pathlib import Path
import pandas as pd
from src.pipeline.backtest import ReverseDCFBacktester, DEFAULT_HORIZONS, COMPREHENSIVE_WACC_MODES

SCENARIOS = [
    ('damodaran_cds',      'Dynamic ERP (CDS-based)'),
    ('damodaran_rating',   'Dynamic ERP (Rating-based)'),
    ('damodaran_size',     'Size Premium Adjusted'),
    ('damodaran_beta',     'Bottom-up Beta Refined'),
    ('damodaran_full',     'Full Comprehensive (Conservative ERP)'),
    ('damodaran_full_cds', 'Full Comprehensive (CDS ERP)'),
    ('damodaran_roic',     'ROIC Quality Screen (EVA)'),
]

HYPOTHESES = {
    'damodaran_cds':      'Time-varying ERP (CDS-based) better captures market risk pricing than static ERP',
    'damodaran_rating':   'Rating-based ERP (conservative) provides more stable discount rates for Thai equities',
    'damodaran_size':     'Small-cap Thai stocks carry additional risk not captured by industry beta alone',
    'damodaran_beta':     'Blended regression+fundamental beta reduces estimation error vs fundamental-only',
    'damodaran_full':     'Full comprehensive Damodaran WACC provides academically superior cost of capital',
    'damodaran_full_cds': 'Full comprehensive with CDS-based ERP provides market-priced cost of capital',
    'damodaran_roic':     'ROIC > WACC quality screen (EVA) selects firms creating economic value, improving signal quality',
}


def run_comprehensive_backtest():
    output_root = Path('research_data/source_of_truth_100/backtest_comprehensive')
    output_root.mkdir(parents=True, exist_ok=True)

    summaries = []
    all_results = {}

    for wacc_mode, label in SCENARIOS:
        scenario_dir = output_root / wacc_mode
        scenario_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"Running scenario: {label} ({wacc_mode})")
        print(f"{'='*60}")

        backtester = ReverseDCFBacktester(
            snapshot_path='research_data/source_of_truth_100/fundamentals_snapshot.csv',
            observations_path='research_data/source_of_truth_100/fundamental_observations.csv',
            price_history_path='research_data/source_of_truth_100/price_history.csv',
            benchmark_history_path='research_data/source_of_truth_100/benchmark_history.csv',
            wacc_mode=wacc_mode,
        )

        result = backtester.run(
            output_dir=str(scenario_dir),
            horizons=DEFAULT_HORIZONS,
            top_n=10,
            rebalance_frequency='Q',
            start_date='2020-01-01',
            case_name=wacc_mode,
        )

        summary = pd.read_csv(scenario_dir / 'summary.csv')
        summary['Scenario_Label'] = label
        summary['WACC_Mode'] = wacc_mode
        summary['Hypothesis'] = HYPOTHESES[wacc_mode]
        summaries.append(summary)
        all_results[wacc_mode] = result

        print(f"  Signals: {result['signals']}")
        print(f"  Portfolio rows: {result['portfolio_rows']}")
        print(f"  Summary:\n{summary[['Horizon_Months', 'Portfolio_Return', 'Benchmark_Return', 'Active_Return', 'Hit_Rate']].to_string(index=False)}")

    # --- Comparison Summary CSV ---
    comparison = pd.concat(summaries, ignore_index=True)
    comparison.to_csv(output_root / 'comparison_summary.csv', index=False, encoding='utf-8-sig')
    print(f"\nComparison summary saved to: {output_root / 'comparison_summary.csv'}")

    # --- Comparison Report ---
    generate_comparison_report(comparison, output_root / 'comparison_report.md')

    # --- Verification ---
    verify_backtest_results(output_root)

    return all_results


def generate_comparison_report(comparison_df: pd.DataFrame, output_path: Path):
    """Generate academic-style comparison report with hypothesis evaluation."""
    lines = [
        '# Comprehensive Damodaran WACC Backtest Comparison Report',
        '',
        '## Methodology',
        '',
        'This report compares 6 WACC construction methodologies based on the Damodaran NYU Stern framework,',
        'applied to a 100-stock Thai SET100 universe with quarterly rebalancing (2021-2026).',
        '',
        'Each scenario isolates a specific WACC dimension to test a hypothesis about cost of capital construction.',
        'The primary metric is **theoretical correctness** (not return optimization).',
        '',
        '### WACC Components Tested',
        '',
        '| Component | Source | Damodaran Reference |',
        '|-----------|--------|-------------------|',
        '| Dynamic ERP (CDS) | ctryprem datasets, 1-year lag | Investment Valuation Ch.7 |',
        '| Dynamic ERP (Rating) | ctryprem datasets, 1-year lag | Investment Valuation Ch.7 |',
        '| Size Premium | Size premium tables, emerging markets | Investment Valuation Ch.8 |',
        '| Blended Beta | betaemerg.xls + 2yr weekly regression | Investment Valuation Ch.7, Damodaran on Valuation Ch.5 |',
        '',
        '### Hypothesis Framework',
        '',
    ]

    for mode, label in SCENARIOS:
        lines.append(f'- **{label}** (`{mode}`): {HYPOTHESES[mode]}')

    lines.extend(['', '---', '', '## Results', ''])

    # --- Table 1: Summary Comparison ---
    lines.append('### Table 1: Summary Comparison')
    lines.append('')
    cols = ['Scenario_Label', 'Horizon_Months', 'Portfolio_Return', 'Benchmark_Return',
            'Active_Return', 'Hit_Rate', 'Observations']
    lines.append('| ' + ' | '.join(cols) + ' |')
    lines.append('| ' + ' | '.join(['---'] * len(cols)) + ' |')
    for _, row in comparison_df.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                vals.append(f'{v:.4f}' if abs(v) < 1 else f'{v:.1f}')
            else:
                vals.append(str(v))
        lines.append('| ' + ' | '.join(vals) + ' |')

    # --- Table 2: vs Baseline Delta ---
    lines.extend(['', '### Table 2: vs Baseline (Fixed 8% WACC) Delta', ''])
    lines.append('Baseline results: Active Return 3M=+1.91%, 6M=+1.99%, 12M=+2.63% | Hit Rate 3M=65%, 6M=55%, 12M=40%')
    lines.append('')
    lines.append('| Scenario | Horizon | Active Return Delta | Hit Rate Delta |')
    lines.append('|----------|---------|--------------------|---------------|')

    baseline_active = {3: 0.019106, 6: 0.019926, 12: 0.026340}
    baseline_hit = {3: 65.0, 6: 55.0, 12: 40.0}

    for _, row in comparison_df.iterrows():
        horizon = int(row['Horizon_Months'])
        ar_delta = float(row['Active_Return']) - baseline_active.get(horizon, 0)
        hr_delta = float(row['Hit_Rate']) - baseline_hit.get(horizon, 0)
        lines.append(f"| {row['Scenario_Label']} | {horizon}M | {ar_delta:+.4f} | {hr_delta:+.1f}pp |")

    # --- Table 3: Hypothesis Evaluation ---
    lines.extend(['', '### Table 3: Hypothesis Evaluation', ''])
    lines.append('| Scenario | Hypothesis | 3M Active Return | 3M Hit Rate | vs Baseline | Assessment |')
    lines.append('|----------|-----------|-----------------|------------|-------------|------------|')

    for mode, label in SCENARIOS:
        row_data = comparison_df[comparison_df['WACC_Mode'] == mode]
        row_3m = row_data[row_data['Horizon_Months'] == 3]
        if not row_3m.empty:
            ar = float(row_3m['Active_Return'].iloc[0])
            hr = float(row_3m['Hit_Rate'].iloc[0])
            vs_base = ar - baseline_active.get(3, 0)
            assessment = 'Positive' if vs_base >= 0 else 'Negative'
            lines.append(f"| {label} | {HYPOTHESES[mode][:50]}... | {ar:.4f} | {hr:.1f}% | {vs_base:+.4f} | {assessment} |")

    # --- No-Lookahead Audit ---
    lines.extend(['', '### No-Lookahead Audit', ''])
    lines.append('All scenarios use 1-year ERP lag rule: rebalance date in year Y uses ERP from year Y-1.')
    lines.append('Dynamic ERP values are sourced from `rdcf/data/thailand_erp_history.csv` with source attribution.')
    lines.append('Regression beta (in `damodaran_beta`, `damodaran_full`, `damodaran_full_cds`) uses only price data on or before rebalance date.')

    # --- Methodology Notes ---
    lines.extend(['', '---', '', '## Methodology Notes', ''])
    lines.append('- **Dynamic ERP**: Time-varying Thailand equity risk premium, lagged 1 year to avoid lookahead bias')
    lines.append('  - CDS-based: Derived from sovereign CDS spreads + mature market implied ERP')
    lines.append('  - Rating-based: Derived from Moody\'s Baa1 rating default spreads + mature market ERP')
    lines.append('- **Size Premium**: Damodaran small-cap premium for emerging markets, applied to trailing market cap')
    lines.append('- **Blended Beta**: 50/50 weight on regression beta (2yr weekly) + fundamental beta (industry unlevered relevered)')
    lines.append('  - Fallback: 100% fundamental beta if regression std error > 0.5 or < 52 weeks data')
    lines.append('  - Boundary: Beta clamped to [0.1, 3.0]')
    lines.append('')
    lines.append('*Report generated by `run_damodaran_comprehensive_backtest.py`*')

    output_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\nComparison report saved to: {output_path}")


def verify_backtest_results(output_root: Path):
    """Run automated verification checks on all scenario outputs."""
    print(f"\n{'='*60}")
    print("VERIFICATION")
    print(f"{'='*60}")

    passed = 0
    failed = 0

    # 1. Scenario completeness
    for mode, _ in SCENARIOS:
        summary_path = output_root / mode / 'summary.csv'
        if summary_path.exists():
            print(f"  [PASS] {mode}: summary.csv exists")
            passed += 1
        else:
            print(f"  [FAIL] {mode}: summary.csv missing")
            failed += 1

    # 2. ERP lag audit (no lookahead)
    for mode in COMPREHENSIVE_WACC_MODES:
        signals_path = output_root / mode / 'signals.csv'
        if signals_path.exists():
            signals = pd.read_csv(signals_path)
            if 'ERP_Lag_Year' in signals.columns:
                rebalance_years = pd.to_datetime(signals['Rebalance_Date']).dt.year
                violations = (signals['ERP_Lag_Year'] >= rebalance_years).sum()
                if violations == 0:
                    print(f"  [PASS] {mode}: ERP lag audit (no lookahead)")
                    passed += 1
                else:
                    print(f"  [FAIL] {mode}: {violations} ERP lookahead violations")
                    failed += 1
            else:
                print(f"  [WARN] {mode}: ERP_Lag_Year column missing (no dynamic ERP)")
        else:
            print(f"  [SKIP] {mode}: signals.csv not found for ERP audit")

    # 3. WACC bounds check
    for mode in COMPREHENSIVE_WACC_MODES:
        signals_path = output_root / mode / 'signals.csv'
        if signals_path.exists():
            signals = pd.read_csv(signals_path)
            if 'WACC' in signals.columns:
                waccs = signals['WACC']
                if (waccs > 0).all() and (waccs < 0.5).all():
                    print(f"  [PASS] {mode}: WACC bounds (0, 0.5)")
                    passed += 1
                else:
                    print(f"  [FAIL] {mode}: WACC out of bounds — min={waccs.min():.4f}, max={waccs.max():.4f}")
                    failed += 1

    # 4. Comparison files
    comp_csv = output_root / 'comparison_summary.csv'
    comp_md = output_root / 'comparison_report.md'
    if comp_csv.exists():
        print(f"  [PASS] comparison_summary.csv exists")
        passed += 1
    else:
        print(f"  [FAIL] comparison_summary.csv missing")
        failed += 1
    if comp_md.exists():
        print(f"  [PASS] comparison_report.md exists")
        passed += 1
    else:
        print(f"  [FAIL] comparison_report.md missing")
        failed += 1

    print(f"\nVerification: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == '__main__':
    results = run_comprehensive_backtest()
    print("\n" + "="*60)
    print("COMPREHENSIVE BACKTEST COMPLETE")
    print("="*60)
