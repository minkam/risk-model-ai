import requests
import time

_last_build = 0
_cached = None

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

YAHOO_SCREENER = "https://query2.finance.yahoo.com/v1/finance/screener/predefined/saved"


def fetch_screener(scr_id, count=100):
    try:
        url = f"{YAHOO_SCREENER}?scrIds={scr_id}&count={count}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()

        quotes = data["finance"]["result"][0]["quotes"]
        return [q["symbol"] for q in quotes if "symbol" in q]

    except Exception:
        return []


def build_universe():
    global _last_build, _cached

    if _cached and time.time() - _last_build < 600:
        return _cached

    gainers = fetch_screener("day_gainers", 100)
    losers = fetch_screener("day_losers", 100)
    actives = fetch_screener("most_actives", 100)

    symbols = list(set(gainers + losers + actives))

    # Filter US only and remove weird tickers
    cleaned = []
    for s in symbols:
        if "." not in s and "-" not in s:
            cleaned.append(s)

    cleaned = cleaned[:250]

    _cached = {
        "all": cleaned
    }

    _last_build = time.time()
    return _cached


def get_top_crypto_usdt(limit=20):
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=10)
        data = r.json()

        data = sorted(
            data,
            key=lambda x: float(x.get("quoteVolume", 0)),
            reverse=True
        )

        top = []
        for item in data:
            sym = item.get("symbol", "")
            if sym.endswith("USDT"):
                base = sym.replace("USDT", "")
                top.append(f"{base}-USD")
            if len(top) >= limit:
                break

        return top

    except Exception:
        return []