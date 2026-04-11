from __future__ import annotations

from typing import Iterable, List, Dict


SET_QUOTE_TEMPLATE = "https://www.set.or.th/en/market/product/stock/quote/{symbol}/price"
SET_FACTSHEET_TEMPLATE = "https://www.set.or.th/en/market/product/stock/quote/{symbol}/factsheet"


def normalize_symbol(ticker: str) -> str:
    """Convert Yahoo .BK tickers into SET page symbols."""
    return ticker.upper().replace('.BK', '').strip()


def build_validation_reference(ticker: str) -> Dict[str, str]:
    """Build optional official SET references for manual QA.

    This module intentionally avoids scraping so the main pipeline remains a
    single-source Yahoo flow; it only records where a human can cross-check.
    """
    symbol = normalize_symbol(ticker)
    return {
        'Ticker': ticker,
        'SET_Symbol': symbol,
        'SET_Price_URL': SET_QUOTE_TEMPLATE.format(symbol=symbol),
        'SET_Factsheet_URL': SET_FACTSHEET_TEMPLATE.format(symbol=symbol),
    }


def build_validation_references(tickers: Iterable[str]) -> List[Dict[str, str]]:
    return [build_validation_reference(ticker) for ticker in tickers]
