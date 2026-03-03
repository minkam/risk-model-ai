import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

FMP_API_KEY = os.getenv("FMP_API_KEY")

print("FMP_API_KEY loaded:", bool(FMP_API_KEY))
BASE_URL = "https://financialmodelingprep.com/api/v3"

_session = requests.Session()
_session.headers.update({"User-Agent": "RiskModelBot/1.0"})

_last_build = 0
_cached = None


def _safe_get(url: str):
    try:
        r = _session.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def _fmp(endpoint: str):
    if not FMP_API_KEY:
        return []
    sep = "&" if "?" in endpoint else "?"
    return _safe_get(f"{BASE_URL}{endpoint}{sep}apikey={FMP_API_KEY}")


def build_universe(limit_each=120):
    """
    Returns dict:
      {
        "large_caps": [...],
        "pennies": [...],
        "momentum": [...],
        "all": [...],
      }
    """
    global _last_build, _cached
    if _cached and time.time() - _last_build < 600:
        return _cached

    if not FMP_API_KEY:
        # Fallback: if no FMP key, return empty and scanner will handle it gracefully.
        _cached = {"large_caps": [], "pennies": [], "momentum": [], "all": []}
        _last_build = time.time()
        return _cached

    # 1) Fresh movers
    gainers = _fmp("/stock_market/gainers")[:limit_each]
    print("FMP gainers length:", len(gainers))
    losers = _fmp("/stock_market/losers")[:limit_each]
    actives = _fmp("/stock_market/actives")[:limit_each]

    raw = []
    raw.extend(gainers)
    raw.extend(losers)
    raw.extend(actives)

    # Normalize symbols
    symbols = []
    for x in raw:
        sym = x.get("symbol")
        if sym and sym.isalpha():
            symbols.append(sym.upper())

    symbols = list(dict.fromkeys(symbols))  # dedupe, keep order

    # 2) Classify with a single screener call per bucket
    # Penny candidates: price 0.5-5, volume > 500k
    pennies = _fmp("/stock-screener?priceMoreThan=0.5&priceLowerThan=5&volumeMoreThan=500000&limit=200")
    penny_syms = [x.get("symbol", "").upper() for x in pennies if x.get("symbol")]
    penny_syms = [s for s in penny_syms if s.isalpha()]

    # Large caps: market cap > 10B, price > 5, volume > 1M
    large = _fmp("/stock-screener?marketCapMoreThan=10000000000&priceMoreThan=5&volumeMoreThan=1000000&limit=200")
    large_syms = [x.get("symbol", "").upper() for x in large if x.get("symbol")]
    large_syms = [s for s in large_syms if s.isalpha()]

    # Momentum bucket = fresh movers + some large + some pennies
    momentum = list(dict.fromkeys(symbols[:150] + large_syms[:100] + penny_syms[:100]))

    all_syms = list(dict.fromkeys(momentum))

    _cached = {
        "large_caps": large_syms[:200],
        "pennies": penny_syms[:200],
        "momentum": momentum[:250],
        "all": all_syms[:250],
    }
    _last_build = time.time()
    return _cached


def get_top_crypto_usdt(limit=25):
    """
    Binance 24h tickers by quoteVolume.
    Returns list like: ["BTCUSDT","ETHUSDT",...]
    """
    try:
        r = _session.get("https://api.binance.com/api/v3/ticker/24hr", timeout=10)
        r.raise_for_status()
        data = r.json()

        data = sorted(data, key=lambda x: float(x.get("quoteVolume", 0) or 0), reverse=True)

        top = []
        for item in data:
            sym = item.get("symbol", "")
            if sym.endswith("USDT"):
                top.append(sym)
            if len(top) >= limit:
                break
        return top
    except Exception:
        return []