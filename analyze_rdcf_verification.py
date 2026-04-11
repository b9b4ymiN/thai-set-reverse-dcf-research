import pandas as pd
import numpy as np
import os

def analyze():
    # File paths
    obs_path = 'research_data/set100_working/fundamental_observations.csv'
    snapshot_path = 'research_data/set100_working/fundamentals_snapshot.csv'
    results_path = 'reverse_dcf_results.csv'
    exclusions_path = 'research_data/set100_working/reverse_dcf_exclusions.csv'

    # Load data
    obs_df = pd.read_csv(obs_path)
    snapshot_df = pd.read_csv(snapshot_path)
    results_df = pd.read_csv(results_path)
    exclusions_df = pd.read_csv(exclusions_path)

    total_stocks = len(snapshot_df)
    tickers = snapshot_df['Ticker'].unique()

    # 1. Fundamental Completeness
    # We'll check snapshots first as they represent the "latest" usable data
    fundamental_metrics = ['Revenue', 'EBIT', 'FCF', 'EPS', 'Total_Debt', 'Total_Cash']
    completeness = {}
    for metric in fundamental_metrics:
        missing_count = snapshot_df[metric].isna().sum() or (snapshot_df[metric] == 0).sum()
        completeness[metric] = {
            'missing': int(missing_count),
            'complete_pct': round((total_stocks - missing_count) / total_stocks * 100, 2)
        }

    # EPS and FCF specific completeness
    eps_complete = snapshot_df[snapshot_df['EPS'] > 0]['Ticker'].nunique()
    fcf_complete = snapshot_df[snapshot_df['FCF'] > 0]['Ticker'].nunique()

    # 2. Reverse DCF Analysis
    total_results = len(results_df)
    pass_validation = len(results_df) # Assuming if it's in results, it passed some basic filter
    
    # Implied growth analysis
    implied_growth = results_df['Implied_Growth_Rate']
    avg_implied_growth = implied_growth.mean()
    median_implied_growth = implied_growth.median()
    
    # Extreme growth rates (> 50% or < -50% might be considered "unreasonable" without further check)
    unreasonable_growth = results_df[(implied_growth > 50) | (implied_growth < -50)]
    
    # 3. Exclusions Analysis
    total_excluded = exclusions_df[exclusions_df['Passes_Reverse_DCF_Filter'] == False]
    exclusion_reasons = total_excluded['Exclusion_Reasons'].value_counts().to_dict()

    # 4. Problematic Stocks
    # Stocks with missing critical data in snapshot
    critical_metrics = ['FCF', 'EPS', 'WACC']
    problem_stocks = snapshot_df[snapshot_df[critical_metrics].isna().any(axis=1) | (snapshot_df['FCF'] <= 0)]['Ticker'].tolist()
    
    # Stocks with extreme implied growth
    extreme_stocks = unreasonable_growth['Ticker'].tolist()

    # Summary Report
    print(f"# RDCF Verification Report - Fundamental & DCF")
    print(f"\n## 1. Data Overview")
    print(f"- Total Stocks in Snapshot: {total_stocks}")
    print(f"- Total Stocks in Results: {total_results}")
    print(f"- Total Stocks in Exclusions List: {len(exclusions_df)}")
    
    print(f"\n## 2. Fundamental Completeness (Snapshot)")
    print("| Metric | Missing/Zero | Completion % |")
    print("|--------|--------------|--------------|")
    for metric, stats in completeness.items():
        print(f"| {metric} | {stats['missing']} | {stats['complete_pct']}% |")

    print(f"\n## 3. Reverse DCF Validation")
    print(f"- Stocks passing filter: {len(exclusions_df[exclusions_df['Passes_Reverse_DCF_Filter'] == True])}")
    print(f"- Stocks failing filter: {len(total_excluded)}")
    print(f"- Average Implied Growth: {avg_implied_growth:.2f}%")
    print(f"- Median Implied Growth: {median_implied_growth:.2f}%")
    print(f"- Stocks with 'Unreasonable' Implied Growth (>50% or <-50%): {len(unreasonable_growth)}")

    print(f"\n## 4. Exclusion Reasons")
    print("| Reason | Count |")
    print("|--------|-------|")
    for reason, count in exclusion_reasons.items():
        print(f"| {reason} | {count} |")

    print(f"\n## 5. Problematic Stocks / Recommendations")
    if problem_stocks:
        print(f"### Missing/Invalid Fundamentals (Critical for DCF):")
        print(", ".join(problem_stocks[:20]) + ("..." if len(problem_stocks) > 20 else ""))
    
    if extreme_stocks:
        print(f"\n### Extreme Implied Growth (Manual Review Recommended):")
        print(", ".join(extreme_stocks[:20]) + ("..." if len(extreme_stocks) > 20 else ""))

    # Save details for visualization hint
    summary_data = {
        'total_stocks': total_stocks,
        'results_stocks': total_results,
        'excluded_stocks': len(total_excluded),
        'completeness': completeness,
        'exclusion_reasons': exclusion_reasons
    }
    
if __name__ == "__main__":
    analyze()
