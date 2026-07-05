"""
India Sector Data — sector scanning for NSE stocks.

Unlike the EGX sector data this replaces (a hardcoded dict of ~18 sectors to
static ticker sets), sector membership here is sourced live from TradingView's
official NSE sectoral indices (``Query().set_index(...)``, verified working:
BANKNIFTY, CNXIT, CNXAUTO, CNXPHARMA, CNXFMCG, CNXMETAL, CNXREALTY, CNXENERGY,
CNXMEDIA, CNXINFRA, CNXPSUBANK, CNXFINANCE). Sector constituents reshuffle
periodically, so a live query avoids the staleness a hardcoded list would
carry. Market-cap weighting (used to build the sector rotation scanner's
weighted market view) is computed from each sector's live aggregate
``market_cap_basic`` rather than a hardcoded weight table.
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional

from tradingview_screener import Query

from tradingview_mcp.core.services.screener_provider import _scan_with_retry

INDIA_SECTORS: Dict[str, str] = {
    "bank": "SYML:NSE;BANKNIFTY",
    "it": "SYML:NSE;CNXIT",
    "auto": "SYML:NSE;CNXAUTO",
    "pharma": "SYML:NSE;CNXPHARMA",
    "fmcg": "SYML:NSE;CNXFMCG",
    "metal": "SYML:NSE;CNXMETAL",
    "realty": "SYML:NSE;CNXREALTY",
    "energy": "SYML:NSE;CNXENERGY",
    "media": "SYML:NSE;CNXMEDIA",
    "infra": "SYML:NSE;CNXINFRA",
    "psu_bank": "SYML:NSE;CNXPSUBANK",
    "financial_services": "SYML:NSE;CNXFINANCE",
}

SECTOR_DISPLAY_NAMES: Dict[str, str] = {
    "bank": "Nifty Bank",
    "it": "Nifty IT",
    "auto": "Nifty Auto",
    "pharma": "Nifty Pharma",
    "fmcg": "Nifty FMCG",
    "metal": "Nifty Metal",
    "realty": "Nifty Realty",
    "energy": "Nifty Energy",
    "media": "Nifty Media",
    "infra": "Nifty Infrastructure",
    "psu_bank": "Nifty PSU Bank",
    "financial_services": "Nifty Financial Services",
}

# Membership + market-cap cache: rebuilt at most once per _CACHE_TTL_S.
_CACHE_TTL_S = 3600.0
_membership_cache: Dict[str, List[str]] = {}
_weight_cache: Dict[str, float] = {}
_reverse_cache: Dict[str, str] = {}
_cache_built_at: float = 0.0


def _refresh_cache_if_stale() -> None:
    global _cache_built_at, _membership_cache, _weight_cache, _reverse_cache
    if _membership_cache and (time.time() - _cache_built_at) < _CACHE_TTL_S:
        return

    membership: Dict[str, List[str]] = {}
    weights: Dict[str, float] = {}
    reverse: Dict[str, str] = {}
    total_cap = 0.0

    for sector_key, index_symbol in INDIA_SECTORS.items():
        try:
            q = Query().set_index(index_symbol).select("name", "market_cap_basic")
            _, df = _scan_with_retry(q, cache_key=("india_sector_v1", sector_key))
            tickers = df["ticker"].tolist()
            cap = float(df["market_cap_basic"].fillna(0).sum())
        except Exception:
            tickers, cap = [], 0.0

        membership[sector_key] = tickers
        weights[sector_key] = cap
        total_cap += cap
        for t in tickers:
            reverse.setdefault(t.upper(), sector_key)

    if total_cap > 0:
        for k in weights:
            weights[k] = round(weights[k] / total_cap * 100, 2)

    if any(membership.values()):
        _membership_cache = membership
        _weight_cache = weights
        _reverse_cache = reverse
        _cache_built_at = time.time()


def get_all_sectors() -> List[str]:
    return sorted(INDIA_SECTORS.keys())


def get_symbols_by_sector(sector_key: str) -> List[str]:
    if sector_key not in INDIA_SECTORS:
        return []
    _refresh_cache_if_stale()
    return _membership_cache.get(sector_key, [])


def get_sector_weight(sector_key: str) -> float:
    """Live market-cap weight (%) of a sector within the tracked sector universe."""
    _refresh_cache_if_stale()
    return _weight_cache.get(sector_key, 0.0)


def get_sector(symbol: str) -> str:
    """Best-effort reverse lookup: which tracked sector a symbol belongs to."""
    _refresh_cache_if_stale()
    return _reverse_cache.get(symbol.upper(), "other")


def get_currency(symbol: str) -> str:
    return "INR"
