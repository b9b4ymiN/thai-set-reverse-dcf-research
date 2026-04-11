#!/usr/bin/env python3
"""
Analyze current fundamental data coverage and create priority stock ranking.
Phase 1: Hybrid Data Strategy - Worker 1 Task

Generates:
- data/processed/metadata/priority_stocks.json (top 20 stocks)
- data/processed/metadata/quarterly_coverage.csv
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List
import yfinance as yf


def load_fundamental_data() -> pd.DataFrame:
    """Load quarterly fundamental data."""
    path = Path("data/processed/fundamentals/quarterly/fundamentals.parquet")
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def calculate_quarters_per_ticker(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate number of quarters available per ticker."""
    if df.empty:
        return pd.DataFrame(columns=['ticker', 'quarter_count'])

    # Count unique fiscal dates per ticker
    quarters = df.groupby('ticker')['fiscal_date'].nunique().reset_index()
    quarters.columns = ['ticker', 'quarter_count']
    return quarters.sort_values('quarter_count', ascending=False)


def load_price_data() -> pd.DataFrame:
    """Load daily price data for liquidity calculation."""
    path = Path("data/processed/prices/daily/prices.parquet")
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path)
    df['date'] = pd.to_datetime(df['date'])
    return df


def calculate_liquidity_scores(price_df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate liquidity score based on average daily trading volume.
    Higher volume = higher liquidity score.
    """
    if price_df.empty:
        return {}

    # Use recent data (last 3 months) for current liquidity
    recent = price_df[price_df['date'] >= '2025-01-01']
    liquidity = recent.groupby('ticker')['volume'].mean().to_dict()

    # Normalize to 0-1 scale
    if liquidity:
        max_vol = max(liquidity.values())
        if max_vol > 0:
            liquidity = {k: v / max_vol for k, v in liquidity.items()}

    return liquidity


def fetch_market_cap_and_sector(tickers: List[str]) -> Dict[str, Dict]:
    """
    Fetch market cap and sector information from Yahoo Finance.
    Returns dict with ticker -> {'market_cap': float, 'sector': str}
    """
    data = {}
    print(f"Fetching market cap and sector data for {len(tickers)} tickers...")

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info or {}
            market_cap = info.get('marketCap') or 0
            sector = info.get('sector') or 'Unknown'
            data[ticker] = {'market_cap': market_cap, 'sector': sector}
        except Exception as e:
            print(f"  Warning: Could not fetch data for {ticker}: {e}")
            data[ticker] = {'market_cap': 0, 'sector': 'Unknown'}

    return data


def calculate_sector_diversity_score(ticker_data: Dict[str, Dict],
                                    tickers: List[str]) -> Dict[str, float]:
    """
    Calculate sector diversity score.
    Stocks in underrepresented sectors get higher scores.
    """
    # Count sectors
    sector_counts = {}
    for ticker in tickers:
        sector = ticker_data.get(ticker, {}).get('sector', 'Unknown')
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    # Calculate diversity score (inverse of sector count)
    max_count = max(sector_counts.values()) if sector_counts else 1
    diversity_scores = {}
    for ticker in tickers:
        sector = ticker_data.get(ticker, {}).get('sector', 'Unknown')
        sector_count = sector_counts.get(sector, 1)
        # Higher score for less represented sectors
        diversity_scores[ticker] = 1 - (sector_count / len(tickers))

    return diversity_scores


def create_priority_ranking(quarters_df: pd.DataFrame,
                           liquidity_scores: Dict[str, float],
                           ticker_data: Dict[str, Dict],
                           diversity_scores: Dict[str, float]) -> pd.DataFrame:
    """
    Create priority ranking using weighted scores:
    - Market cap: 50%
    - Existing quarters: 30%
    - Liquidity: 10%
    - Sector diversity: 10%
    """
    results = []

    # Normalize market caps to 0-1 scale
    market_caps = {t: d['market_cap'] for t, d in ticker_data.items()}
    max_mc = max(market_caps.values()) if market_caps else 1
    if max_mc > 0:
        market_caps = {t: v / max_mc for t, v in market_caps.items()}

    # Normalize quarter counts to 0-1 scale
    max_quarters = quarters_df['quarter_count'].max() if not quarters_df.empty else 1
    if max_quarters > 0:
        quarters_df['normalized_quarters'] = quarters_df['quarter_count'] / max_quarters
    else:
        quarters_df['normalized_quarters'] = 0

    for ticker in quarters_df['ticker']:
        mc_score = market_caps.get(ticker, 0)
        q_score = quarters_df[quarters_df['ticker'] == ticker]['normalized_quarters'].values[0]
        liq_score = liquidity_scores.get(ticker, 0)
        div_score = diversity_scores.get(ticker, 0)

        # Weighted score
        final_score = (
            mc_score * 0.50 +
            q_score * 0.30 +
            liq_score * 0.10 +
            div_score * 0.10
        )

        results.append({
            'ticker': ticker,
            'quarter_count': quarters_df[quarters_df['ticker'] == ticker]['quarter_count'].values[0],
            'market_cap_bht': ticker_data.get(ticker, {}).get('market_cap', 0) / 1e9,  # Convert to billions
            'sector': ticker_data.get(ticker, {}).get('sector', 'Unknown'),
            'liquidity_score': liq_score,
            'diversity_score': div_score,
            'market_cap_score': mc_score,
            'quarters_score': q_score,
            'final_score': final_score
        })

    ranking_df = pd.DataFrame(results)
    ranking_df = ranking_df.sort_values('final_score', ascending=False).reset_index(drop=True)
    return ranking_df


def save_outputs(ranking_df: pd.DataFrame, quarters_df: pd.DataFrame):
    """Save output files."""
    output_dir = Path("data/processed/metadata")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save top 20 priority stocks as JSON
    top_20 = ranking_df.head(20)
    priority_stocks = {
        'generated_at': pd.Timestamp.now().isoformat(),
        'total_analyzed': len(ranking_df),
        'top_20_stocks': top_20.to_dict('records')
    }

    with open(output_dir / 'priority_stocks.json', 'w') as f:
        json.dump(priority_stocks, f, indent=2, default=str)

    print(f"✅ Saved priority_stocks.json with top 20 stocks")

    # Save quarterly coverage CSV
    coverage_df = quarters_df[['ticker', 'quarter_count']].copy() if 'quarter_count' in quarters_df.columns else quarters_df.copy()
    coverage_df = coverage_df.sort_values('ticker')
    coverage_df.to_csv(output_dir / 'quarterly_coverage.csv', index=False)
    print(f"✅ Saved quarterly_coverage.csv with {len(coverage_df)} tickers")

    # Print summary
    print(f"\n📊 COVERAGE SUMMARY:")
    print(f"  Total tickers analyzed: {len(ranking_df)}")
    print(f"  Average quarters per ticker: {ranking_df['quarter_count'].mean():.1f}")
    print(f"  Total market cap: {ranking_df['market_cap_bht'].sum():.1f}B THB")
    print(f"\n🏆 TOP 10 PRIORITY STOCKS:")
    print(top_20[['ticker', 'quarter_count', 'market_cap_bht', 'sector', 'final_score']].to_string(index=False))


def main():
    """Main execution function."""
    print("=" * 60)
    print("PHASE 1: Data Coverage Analysis & Priority Stock Ranking")
    print("=" * 60)

    # Load data
    print("\n📂 Loading data...")
    fund_df = load_fundamental_data()
    if fund_df.empty:
        print("❌ No fundamental data found!")
        return

    price_df = load_price_data()

    # Calculate metrics
    print("📊 Calculating quarterly coverage...")
    quarters_df = calculate_quarters_per_ticker(fund_df)

    print("💧 Calculating liquidity scores...")
    liquidity_scores = calculate_liquidity_scores(price_df)

    print("🏢 Fetching market cap and sector data...")
    tickers = quarters_df['ticker'].tolist()
    ticker_data = fetch_market_cap_and_sector(tickers)

    print("🌈 Calculating sector diversity scores...")
    diversity_scores = calculate_sector_diversity_score(ticker_data, tickers)

    # Create ranking
    print("🎯 Creating priority ranking...")
    ranking_df = create_priority_ranking(
        quarters_df,
        liquidity_scores,
        ticker_data,
        diversity_scores
    )

    # Save outputs
    save_outputs(ranking_df, quarters_df)

    print("\n✅ Analysis complete!")
    print(f"   - Priority stocks: data/processed/metadata/priority_stocks.json")
    print(f"   - Coverage report: data/processed/metadata/quarterly_coverage.csv")


if __name__ == "__main__":
    main()
