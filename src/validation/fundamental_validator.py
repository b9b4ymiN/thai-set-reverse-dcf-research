import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

class FundamentalValidator:
    """
    Validation framework for fundamental data to ensure quality and completeness.
    """

    def __init__(self, target_quarters: int = 16, target_annual: int = 4):
        self.target_quarters = target_quarters
        self.target_annual = target_annual

    def validate_completeness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check if each ticker has enough records."""
        results = {}
        for ticker in df['ticker'].unique():
            ticker_df = df[df['ticker'] == ticker]
            
            annual_dates = ticker_df[ticker_df['period_type'] == 'annual']['fiscal_date'].unique()
            quarterly_dates = ticker_df[ticker_df['period_type'] == 'quarterly']['fiscal_date'].unique()
            
            results[ticker] = {
                'annual_count': len(annual_dates),
                'quarterly_count': len(quarterly_dates),
                'is_complete': (len(annual_dates) >= self.target_annual and 
                               len(quarterly_dates) >= self.target_quarters)
            }
        return results

    def detect_outliers(self, df: pd.DataFrame, threshold: float = 3.0) -> List[Dict[str, Any]]:
        """Detect >300% changes in metrics between consecutive periods."""
        outliers = []
        for (ticker, item, ptype), group in df.groupby(['ticker', 'item_name', 'period_type']):
            if len(group) < 2:
                continue
            
            group = group.sort_values('fiscal_date')
            # Handle zeros to avoid inf
            values = group['value'].replace(0, np.nan)
            pct_change = values.pct_change().abs()
            
            for idx, change in pct_change.items():
                if not np.isnan(change) and change > threshold:
                    outliers.append({
                        'ticker': ticker,
                        'item_name': item,
                        'period_type': ptype,
                        'date': group.loc[idx, 'fiscal_date'],
                        'change_multiple': round(change, 2),
                        'value': group.loc[idx, 'value']
                    })
        return outliers

    def validate_accounting_sanity(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Check for basic accounting logic (e.g. Net Debt = Total Debt - Total Cash)."""
        issues = []
        # Need wide format for this
        wide = df.pivot_table(
            index=['ticker', 'fiscal_date', 'period_type'],
            columns='item_name',
            values='value'
        ).reset_index()
        
        # Check Net Debt = Total Debt - Total Cash
        if 'net_debt' in wide.columns and 'total_debt' in wide.columns and 'total_cash' in wide.columns:
            # Using 1% tolerance for rounding
            diff = (wide['net_debt'] - (wide['total_debt'] - wide['total_cash'])).abs()
            mask = diff > (wide['total_debt'].abs() * 0.01)
            
            for _, row in wide[mask].iterrows():
                issues.append({
                    'ticker': row['ticker'],
                    'date': row['fiscal_date'],
                    'type': 'accounting_mismatch',
                    'message': f"Net Debt ({row['net_debt']}) != Total Debt - Cash ({row['total_debt'] - row['total_cash']})"
                })
        
        return issues

    def run_validation_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        print("🔍 Starting data validation...")
        completeness = self.validate_completeness(df)
        outliers = self.detect_outliers(df)
        accounting = self.validate_accounting_sanity(df)
        
        total_tickers = len(df['ticker'].unique())
        complete_count = sum(1 for r in completeness.values() if r['is_complete'])
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tickers': total_tickers,
                'complete_tickers': complete_count,
                'completeness_pct': round(complete_count / total_tickers * 100, 2) if total_tickers > 0 else 0,
                'outlier_count': len(outliers),
                'accounting_issues': len(accounting)
            },
            'outliers_sample': outliers[:10],
            'accounting_issues_sample': accounting[:10]
        }
        return report

if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.getcwd())
    from src.storage.fundamental_store import FundamentalStore
    
    store = FundamentalStore(data_path="data/processed/fundamentals.parquet")
    df = store.load_raw()
    
    validator = FundamentalValidator()
    report = validator.run_validation_report(df)
    
    print(f"\n✅ Validation Summary:")
    print(f"   Tickers: {report['summary']['total_tickers']}")
    print(f"   Complete (4Y+16Q): {report['summary']['complete_tickers']} ({report['summary']['completeness_pct']}%)")
    print(f"   Outliers (>300% change): {report['summary']['outlier_count']}")
    print(f"   Accounting Issues: {report['summary']['accounting_issues']}")
