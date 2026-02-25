import time
from typing import Dict, List, Optional, Tuple

import requests
import yfinance as yf
import pandas as pd


# ----------------------------
# STOCK UNIVERSE (BIGGER LIST)
# ----------------------------
# Add/remove tickers freely. This is intentionally "large but reasonable".
# If you want "auto-discover" later, we can add a screener API — but this works now.
STOCKS: List[str] = [
    # Index ETFs / Mega liquid
    "SPY", "QQQ", "IWM", "DIA",
    # Mega cap tech
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
    "AMD", "AVGO", "NFLX", "CRM", "ORCL", "INTC",
    # Finance
    "JPM", "BAC", "WFC", "GS", "MS", "COIN",
    # Energy
    "XOM", "CVX", "OXY",
    # Health
    "UNH", "LLY", "JNJ", "PFE",
    # Popular / high beta
    "PLTR", "SOFI", "RIVN", "LCID", "NIO",
    "GME", "AMC",
    # Semis / AI adjacents
    "SMCI", "ARM", "MU",
    # Gold / miners
    "GLD", "SLV",
]

# ----------------------------
# CRYPTO SETTINGS (COINGECKO)
# ----------------------------
COINGECKO_BASE = "https://api.coingecko.com/api/v3"


def _safe_float(x, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _yf_last_close(symbol: str) -> Optional[Tuple[float, float, float]]:
    """
    Returns (last_close, prev_close, volume) using yfinance 5d daily bars.
    """
    try:
        df = yf.download(symbol, period="5d", interval="1d", progress=False, auto_adjust=False)
        if df is None or df.empty:
            return None
        # Ensure we have at least 2 daily closes
        df = df.dropna()
        if len(df) < 2:
            return None

        last_close = float(df["Close"].iloc[-1])
        prev_close = float(df["Close"].iloc[-2])

        vol = 0.0
        if "Volume" in df.columns:
            vol = float(df["Volume"].iloc[-1]) if pd.notna(df["Volume"].iloc[-1]) else 0.0

        return last_close, prev_close, vol
    except Exception:
        return None


def _pct_change(last_close: float, prev_close: float) -> float:
    if prev_close == 0:
        return 0.0
    return ((last_close - prev_close) / prev_close) * 100.0


# ----------------------------
# STOCK MOVERS / SETUPS
# ----------------------------
def get_stock_movers(limit: int = 5) -> List[Dict]:
    """
    Scans STOCKS and returns top gainers by 1D % change with close + % + volume.
    """
    movers: List[Dict] = []
    for t in STOCKS:
        info = _yf_last_close(t)
        if not info:
            continue
        last_close, prev_close, vol = info
        chg = _pct_change(last_close, prev_close)

        movers.append({
            "symbol": t,
            "price": round(last_close, 2),
            "pct": round(chg, 2),
            "volume": int(vol),
        })

        # tiny sleep reduces rate-limit pain
        time.sleep(0.05)

    movers.sort(key=lambda x: x["pct"], reverse=True)
    return movers[:limit]


def stock_setups(limit: int = 10) -> List[Dict]:
    """
    Basic 'setup' logic:
      - 1D change >= +2%
      - volume not tiny (>= 1,000,000 for stocks, ETFs will pass easily)
    You can tighten/loosen later.
    """
    setups: List[Dict] = []
    for t in STOCKS:
        info = _yf_last_close(t)
        if not info:
            continue
        last_close, prev_close, vol = info
        chg = _pct_change(last_close, prev_close)

        # Setup filters
        if chg >= 2.0 and vol >= 1_000_000:
            setups.append({
                "symbol": t,
                "direction": "LONG",
                "price": round(last_close, 2),
                "pct": round(chg, 2),
                "volume": int(vol),
                "note": "Strong green day + liquid volume"
            })

        time.sleep(0.05)

    setups.sort(key=lambda x: x["pct"], reverse=True)
    return setups[:limit]


# ----------------------------
# CRYPTO MOVERS / SETUPS
# ----------------------------
def _coingecko_markets(vs: str = "usd", per_page: int = 200, page: int = 1) -> List[Dict]:
    url = f"{COINGECKO_BASE}/coins/markets"
    params = {
        "vs_currency": vs,
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": page,
        "sparkline": "false",
        "price_change_percentage": "24h,7d",
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def get_crypto_movers(limit: int = 5) -> List[Dict]:
    """
    Top 200 by market cap (CoinGecko), rank by 24h % change.
    Also includes price + 24h volume + 7d %.
    """
    try:
        data = _coingecko_markets(per_page=200, page=1)
    except Exception:
        return []

    movers: List[Dict] = []
    for c in data:
        pct24 = _safe_float(c.get("price_change_percentage_24h"))
        pct7d = _safe_float(c.get("price_change_percentage_7d_in_currency"))
        movers.append({
            "symbol": (c.get("symbol") or "").upper(),
            "name": c.get("name") or "",
            "price": round(_safe_float(c.get("current_price")), 6),
            "pct_24h": round(pct24, 2),
            "pct_7d": round(pct7d, 2),
            "vol_24h": int(_safe_float(c.get("total_volume"))),
            "mcap": int(_safe_float(c.get("market_cap"))),
        })

    movers.sort(key=lambda x: x["pct_24h"], reverse=True)
    return movers[:limit]


def crypto_setups(limit: int = 10) -> List[Dict]:
    """
    Setup logic (simple + useful):
      - top 200 by mcap
      - 24h % >= +5%
      - 24h volume >= $250M (filters out illiquid noise)
    """
    try:
        data = _coingecko_markets(per_page=200, page=1)
    except Exception:
        return []

    setups: List[Dict] = []
    for c in data:
        pct24 = _safe_float(c.get("price_change_percentage_24h"))
        vol = _safe_float(c.get("total_volume"))
        price = _safe_float(c.get("current_price"))
        pct7d = _safe_float(c.get("price_change_percentage_7d_in_currency"))

        if pct24 >= 5.0 and vol >= 250_000_000:
            setups.append({
                "symbol": (c.get("symbol") or "").upper(),
                "name": c.get("name") or "",
                "direction": "LONG",
                "price": round(price, 6),
                "pct_24h": round(pct24, 2),
                "pct_7d": round(pct7d, 2),
                "vol_24h": int(vol),
                "note": "Big 24h momentum + high volume"
            })

    setups.sort(key=lambda x: x["pct_24h"], reverse=True)
    return setups[:limit]


# ----------------------------
# REPORTS
# ----------------------------
def generate_eod_report() -> str:
    """
    End of day: Top 5 stock gainers (from our universe) + Top 5 crypto gainers (top 200 mcap).
    """
    stock_movers = get_stock_movers(limit=5)
    crypto_movers = get_crypto_movers(limit=5)

    lines = []
    lines.append("📊 END OF DAY REPORT\n")
    lines.append("🔥 Top Stock Gainers Today:")
    if not stock_movers:
        lines.append("No data available.")
    else:
        for m in stock_movers:
            lines.append(f"- {m['symbol']}: ${m['price']} ({m['pct']}%), Vol {m['volume']:,}")

    lines.append("\n🪙 Top Crypto Gainers Today:")
    if not crypto_movers:
        lines.append("No data available.")
    else:
        for m in crypto_movers:
            lines.append(f"- {m['symbol']} ({m['name']}): ${m['price']} ({m['pct_24h']}% 24h, {m['pct_7d']}% 7d), Vol ${m['vol_24h']:,}")

    return "\n".join(lines)


def generate_open_report() -> str:
    """
    Market open: show early momentum using same ranking, but label as "Early".
    For stocks, yfinance daily data won't be truly 'open' intraday unless you use 5m bars.
    We'll do "yesterday->today" daily change as early proxy.
    """
    stock_movers = get_stock_movers(limit=5)
    crypto_movers = get_crypto_movers(limit=5)

    lines = []
    lines.append("🔔 MARKET OPEN REPORT\n")
    lines.append("🚀 Early Stock Momentum:")
    if not stock_movers:
        lines.append("No early data.")
    else:
        for m in stock_movers:
            lines.append(f"- {m['symbol']}: ${m['price']} ({m['pct']}%), Vol {m['volume']:,}")

    lines.append("\n🪙 Early Crypto Momentum:")
    if not crypto_movers:
        lines.append("No early data.")
    else:
        for m in crypto_movers:
            lines.append(f"- {m['symbol']} ({m['name']}): ${m['price']} ({m['pct_24h']}% 24h, {m['pct_7d']}% 7d), Vol ${m['vol_24h']:,}")

    return "\n".join(lines)


# ----------------------------
# MASTER SCAN (for /scan + auto alerts)
# ----------------------------
def scan_market() -> Dict[str, List[Dict]]:
    """
    Always returns dict with keys: 'stocks', 'crypto'
    """
    return {
        "stocks": stock_setups(limit=10),
        "crypto": crypto_setups(limit=10),
    }