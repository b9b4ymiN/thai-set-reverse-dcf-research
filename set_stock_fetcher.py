#!/usr/bin/env python3
"""
SET Thailand Stock Data Fetcher for Reverse DCF Analysis

Primary datasource: Yahoo Finance via yfinance
Optional validation references: official SET quote/factsheet pages
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

import pandas as pd

from rdcf.data_sources import (
    YahooFinanceSource,
    build_datasource_quality_report,
    build_reverse_dcf_exclusion_report,
    build_validation_references,
)


class SETStockFetcher:
    """Fetch Thai SET100 stock snapshot data for reverse DCF analysis."""

    SET_TICKERS = [
        'ADVANC.BK',
        'AKR.BK',
        'AOT.BK',
        'AP.BK',
        'ASAP.BK',
        'ASIAN.BK',
        'AWC.BK',
        'BANPU.BK',
        'BAY.BK',
        'BBL.BK',
        'BCH.BK',
        'BCPG.BK',
        'BCT.BK',
        'BDMS.BK',
        'BEM.BK',
        'BGRIM.BK',
        'BH.BK',
        'BJC.BK',
        'BRR.BK',
        'BTS.BK',
        'CBG.BK',
        'CCET.BK',
        'CENTEL.BK',
        'CGD.BK',
        'CHG.BK',
        'CIMBT.BK',
        'COM7.BK',
        'CPALL.BK',
        'CPF.BK',
        'CPN.BK',
        'CRC.BK',
        'DELTA.BK',
        'DRT.BK',
        'EA.BK',
        'EGCO.BK',
        'ERW.BK',
        'FPI.BK',
        'FPT.BK',
        'GLOBAL.BK',
        'GPI.BK',
        'GPSC.BK',
        'GULF.BK',
        'HANA.BK',
        'HMPRO.BK',
        'IRPC.BK',
        'ITD.BK',
        'IVL.BK',
        'JAS.BK',
        'JMART.BK',
        'JMT.BK',
        'KBANK.BK',
        'KBS.BK',
        'KCE.BK',
        'KKP.BK',
        'KSL.BK',
        'KTB.BK',
        'KTC.BK',
        'LH.BK',
        'MEGA.BK',
        'MINT.BK',
        'MTC.BK',
        'NCH.BK',
        'NOBLE.BK',
        'OR.BK',
        'OSP.BK',
        'PF.BK',
        'PG.BK',
        'PRIN.BK',
        'PSL.BK',
        'PTT.BK',
        'PTTEP.BK',
        'PTTGC.BK',
        'RATCH.BK',
        'RBF.BK',
        'RCL.BK',
        'RML.BK',
        'RS.BK',
        'SAWAD.BK',
        'SCB.BK',
        'SCC.BK',
        'SCGP.BK',
        'SITHAI.BK',
        'SPALI.BK',
        'SPRC.BK',
        'STPI.BK',
        'TCAP.BK',
        'THANI.BK',
        'TIDLOR.BK',
        'TISCO.BK',
        'TLI.BK',
        'TOP.BK',
        'TR.BK',
        'TRUE.BK',
        'TTB.BK',
        'TU.BK',
        'TVO.BK',
        'VGI.BK',
        'WHA.BK',
        'WPH.BK',
        'XPG.BK'
    ]

    def __init__(self, source: Optional[YahooFinanceSource] = None, sleep_seconds: float = 0.5):
        self.source = source or YahooFinanceSource()
        self.sleep_seconds = sleep_seconds
        self.data: List[Dict] = []

    @staticmethod
    def _deduplicate_tickers(tickers: List[str]) -> List[str]:
        """Preserve order while removing duplicate tickers."""
        return list(dict.fromkeys(tickers))

    def get_stock_data(self, ticker: str) -> Optional[Dict]:
        """Fetch normalized stock data for one ticker."""
        print(f"Fetching {ticker}...")
        return self.source.fetch_stock_data(ticker)

    def fetch_all_stocks(self, tickers: List[str] = None) -> pd.DataFrame:
        """Fetch data for all specified tickers."""
        tickers = self._deduplicate_tickers(tickers or self.SET_TICKERS)

        print(f"Fetching data for {len(tickers)} stocks...")
        print("=" * 50)

        rows: List[Dict] = []
        for index, ticker in enumerate(tickers, 1):
            stock_data = self.get_stock_data(ticker)
            if stock_data:
                rows.append(stock_data)

            if self.sleep_seconds:
                time.sleep(self.sleep_seconds)

            if index % 10 == 0:
                print(f"Progress: {index}/{len(tickers)}")

        self.data = rows
        df = pd.DataFrame(rows)
        print(f"\nSuccessfully fetched {len(df)} stocks")
        return df

    def save_to_csv(self, df: pd.DataFrame, filename: str = 'set_stock_data.csv'):
        """Save fetched snapshot data to CSV."""
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"Data saved to {filename}")

    def save_quality_reports(
        self,
        df: pd.DataFrame,
        quality_filename: str = 'set_stock_data_quality.csv',
        exclusions_filename: str = 'reverse_dcf_input_exclusions.csv',
        validation_filename: str = 'set_validation_references.csv',
    ):
        """Save datasource quality and validation-reference artifacts."""
        quality_report = build_datasource_quality_report(df)
        quality_report.to_csv(quality_filename, index=False, encoding='utf-8-sig')

        exclusion_report = build_reverse_dcf_exclusion_report(df)
        exclusion_report.to_csv(exclusions_filename, index=False, encoding='utf-8-sig')

        validation_references = pd.DataFrame(build_validation_references(df['Ticker'].tolist()))
        validation_references.to_csv(validation_filename, index=False, encoding='utf-8-sig')

        print(f"Quality report saved to {quality_filename}")
        print(f"Exclusion report saved to {exclusions_filename}")
        print(f"Validation references saved to {validation_filename}")

    def get_summary_stats(self, df: pd.DataFrame):
        """Display summary statistics for the snapshot dataset."""
        print("\n" + "=" * 50)
        print("SUMMARY STATISTICS")
        print("=" * 50)

        numeric_cols = [
            'Current_Price', 'Market_Cap', 'EPS', 'PE_Ratio',
            'Revenue_Growth', 'ROE', 'WACC', 'Dividend_Yield',
        ]

        for col in numeric_cols:
            if col in df.columns:
                # Ensure column is numeric
                df[col] = pd.to_numeric(df[col], errors='coerce')
                print(f"\n{col}:")
                print(f"  Mean: {df[col].mean():.2f}")
                print(f"  Median: {df[col].median():.2f}")
                print(f"  Min: {df[col].min():.2f}")
                print(f"  Max: {df[col].max():.2f}")

        if not df.empty:
            exclusion_report = build_reverse_dcf_exclusion_report(df)
            excluded = exclusion_report[~exclusion_report['Passes_Reverse_DCF_Filter']]
            print(f"\nReverse DCF-ready rows: {len(df) - len(excluded)}/{len(df)}")
            if not excluded.empty:
                print("Top exclusion reasons:")
                print(excluded['Exclusion_Reasons'].value_counts().head(5).to_string())


def main():
    """Main execution function."""
    fetcher = SETStockFetcher()
    df = fetcher.fetch_all_stocks()

    if not df.empty:
        fetcher.save_to_csv(df, 'set_stock_data.csv')
        fetcher.save_quality_reports(df)
        fetcher.get_summary_stats(df)

        print("\n" + "=" * 50)
        print("SAMPLE DATA (First 5 stocks)")
        print("=" * 50)
        print(df[['Ticker', 'Company_Name', 'Current_Price', 'EPS', 'PE_Ratio', 'Revenue_Growth', 'ROE', 'WACC']].head().to_string())

        print("\n" + "=" * 50)
        print("✓ Data ready for DCF Analysis!")
        print(f"✓ Total stocks: {len(df)}")
        print("✓ Files:")
        print("  - set_stock_data.csv")
        print("  - set_stock_data_quality.csv")
        print("  - reverse_dcf_input_exclusions.csv")
        print("  - set_validation_references.csv")
        print("=" * 50)
    else:
        print("No data fetched. Please check your internet connection.")


if __name__ == "__main__":
    main()
