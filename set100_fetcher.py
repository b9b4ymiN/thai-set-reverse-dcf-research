#!/usr/bin/env python3
"""
SET100 Stock Fetcher - Fetches all 100 SET stocks
"""

from set_stock_fetcher import SETStockFetcher
import pandas as pd

# Full SET100 list (100 stocks)
SET100_TICKERS = [
    'ADVANC.BK',
    'AOT.BK',
    'AWC.BK',
    'BANPU.BK',
    'BBL.BK',
    'BDMS.BK',
    'BEM.BK',
    'BGRIM.BK',
    'BH.BK',
    'BJC.BK',
    'BTS.BK',
    'CBG.BK',
    'CCET.BK',
    'CENTEL.BK',
    'COM7.BK',
    'CPALL.BK',
    'CPF.BK',
    'CPN.BK',
    'DELTA.BK',
    'EA.BK',
    'EGCO.BK',
    'GLOBAL.BK',
    'GPSC.BK',
    'GULF.BK',
    'HMPRO.BK',
    'IVL.BK',
    'KBANK.BK',
    'KCE.BK',
    'KKP.BK',
    'KTB.BK',
    'KTC.BK',
    'LH.BK',
    'MINT.BK',
    'OR.BK',
    'OSP.BK',
    'PTT.BK',
    'RATCH.BK',
    'SAWAD.BK',
    'SCB.BK',
    'SCC.BK',
    'SCGP.BK',
    'TCAP.BK',
    'TIDLOR.BK',
    'TISCO.BK',
    'TLI.BK',
    'TOP.BK',
    'TRUE.BK',
    'TTB.BK',
    'TU.BK',
    'VGI.BK',
    'PTTEP.BK',
    'PTTGC.BK',
    'WHA.BK',
    'BAY.BK',
    'BANK.BK',
    'CIMBT.BK',
    'CIP.BK',
    'CRC.BK',
    'DRT.BK',
    'FPT.BK',
    'IFEC.BK',
    'JMT.BK',
    'KSL.BK',
    'LHB.BK',
    'MAK.BK',
    'MK.BK',
    'MTC.BK',
    'NCH.BK',
    'PF.BK',
    'PG.BK',
    'PLAN.BK',
    'PRIN.BK',
    'PSL.BK',
    'RBF.BK',
    'RCL.BK',
    'RS.BK',
    'SPALI.BK',
    'SPRC.BK',
    'STPI.BK',
    'TFF.BK',
    'THANI.BK',
    'TID.BK',
    'TIP.BK',
    'TMB.BK',
    'TPI.BK',
    'TR.BK',
    'TVO.BK',
    'UOB.BK',
    'WPH.BK',
    'XPG.BK',
    'YUWTA.BK',
    'BCH.BK',
    'BCPG.BK',
    'BRR.BK',
    'CGD.BK',
    'CHG.BK',
    'ERW.BK',
    'FPI.BK',
    'GLOW.BK',
    'GPI.BK'
]

def main():
    """Fetch all SET100 stocks."""
    print("=" * 60)
    print("SET100 STOCK DATA FETCHER")
    print("=" * 60)
    print(f"Total stocks to fetch: {len(SET100_TICKERS)}")
    print("This will take approximately 30-45 minutes")
    print("=" * 60)
    
    fetcher = SETStockFetcher(sleep_seconds=0.3)
    
    # Fetch in batches of 25
    batch_size = 25
    all_data = []
    
    for i in range(0, len(SET100_TICKERS), batch_size):
        batch = SET100_TICKERS[i:i+batch_size]
        batch_num = i//batch_size + 1
        total_batches = (len(SET100_TICKERS)-1)//batch_size + 1
        
        print(f"\\n{'='*60}")
        print(f"BATCH {batch_num}/{total_batches}")
        print(f"Stocks {i+1}-{min(i+batch_size, len(SET100_TICKERS))}")
        print(f"{'='*60}")
        
        df_batch = fetcher.fetch_all_stocks(batch)
        if not df_batch.empty:
            all_data.append(df_batch)
            print(f"✅ Batch {batch_num} complete: {len(df_batch)} stocks")
    
    # Combine all batches
    if all_data:
        df_final = pd.concat(all_data, ignore_index=True)
        
        print(f"\\n{'='*60}")
        print("SAVING RESULTS")
        print(f"{'='*60}")
        
        fetcher.save_to_csv(df_final, 'set100_stock_data.csv')
        fetcher.save_quality_reports(
            df_final,
            quality_filename='set100_stock_data_quality.csv',
            exclusions_filename='set100_reverse_dcf_exclusions.csv',
            validation_filename='set100_validation_references.csv'
        )
        fetcher.get_summary_stats(df_final)
        
        print(f"\\n{'='*60}")
        print(f"✅ SET100 COMPLETE: {len(df_final)} stocks fetched")
        print(f"📊 Data saved to set100_stock_data.csv")
        print(f"{'='*60}")
        
        # Show sample
        print(f"\\nSAMPLE DATA (First 5 stocks):")
        print(df_final[['Ticker', 'Company_Name', 'Current_Price', 'EPS', 'PE_Ratio']].head().to_string())
    else:
        print("❌ No data fetched")

if __name__ == "__main__":
    main()
