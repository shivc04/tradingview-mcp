"""
India Index Data — NIFTY 50 (NSE) and SENSEX (BSE) constituent lookups.

Unlike the EGX index data this replaces, constituents are fetched live from
TradingView's screener index endpoint (``Query().set_index(...)``) instead of
a hardcoded list. Index membership is reshuffled periodically (semi-annually
for NIFTY 50; similarly for SENSEX), so a static list would silently go
stale — a live query never does.
"""
from __future__ import annotations

from typing import Dict, List

from tradingview_screener import Query

from tradingview_mcp.core.services.screener_provider import _scan_with_retry

# TradingView index symbols, syntax `SYML:{source};{symbol}` — verified live:
# SYML:NSE;NIFTY -> 50 rows (NSE:...), SYML:BSE;SENSEX -> 30 rows (BSE:...)
_INDEX_SYMBOLS: Dict[str, str] = {
    "NIFTY50": "SYML:NSE;NIFTY",
    "SENSEX": "SYML:BSE;SENSEX",
}


def _fetch_index_constituents(index_symbol: str, cache_key: str) -> List[str]:
    """Fetch current constituent tickers for a TradingView index symbol."""
    try:
        q = Query().set_index(index_symbol).select("name")
        _, df = _scan_with_retry(q, cache_key=("india_index_v1", cache_key))
        return df["ticker"].tolist()
    except Exception:
        return []


def get_nifty50_symbols() -> List[str]:
    return _fetch_index_constituents(_INDEX_SYMBOLS["NIFTY50"], "NIFTY50")


def get_sensex_symbols() -> List[str]:
    return _fetch_index_constituents(_INDEX_SYMBOLS["SENSEX"], "SENSEX")


INDIA_INDICES: Dict[str, dict] = {
    "NIFTY50": {
        "name": "NIFTY 50",
        "description": "NSE's flagship 50-stock benchmark index.",
        "get_symbols": get_nifty50_symbols,
        "constituents_count": 50,
    },
    "SENSEX": {
        "name": "S&P BSE SENSEX",
        "description": "BSE's flagship 30-stock benchmark index.",
        "get_symbols": get_sensex_symbols,
        "constituents_count": 30,
    },
}
