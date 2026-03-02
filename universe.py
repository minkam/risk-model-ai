import requests
import yfinance as yf
import time

last_build = 0
cached_universe = None


# ==============================
# SAFE REQUEST
# ==============================

def safe_get(url):
    try:
        r = requests.get(url, timeout=5)
        return r.json()
    except:
        return []


# ==============================
# YAHOO MOST ACTIVE
# ==============================

def get_most_active():
    try:
        url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?count=50&scrIds=most_actives"
        data = safe_get(url)

        quotes = data["finance"]["result"][0]["quotes"]

        symbols = []
        for q in quotes:
            price = q.get("regularMarketPrice", 0)
            if price and price > 1:
                symbols.append(q["symbol"])

        return symbols[:40]

    except:
        return []


# ==============================
# YAHOO TOP GAINERS
# ==============================

def get_top_gainers():
    try:
        url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?count=50&scrIds=day_gainers"
        data = safe_get(url)

        quotes = data["finance"]["result"][0]["quotes"]

        symbols = []
        for q in quotes:
            change = q.get("regularMarketChangePercent", 0)
            price = q.get("regularMarketPrice", 0)

            if price and change and change > 3:
                symbols.append(q["symbol"])

        return symbols[:40]

    except:
        return []


# ==============================
# PENNY BREAKOUT FILTER
# ==============================

def get_penny_breakouts():
    try:
        gainers = get_top_gainers()

        data = yf.download(
            gainers,
            period="5d",
            interval="1d",
            group_by="ticker",
            progress=False,
            threads=True
        )

        pennies = []

        for symbol in gainers:
            try:
                df = data[symbol]
                if df.empty:
                    continue

                price = float(df["Close"].iloc[-1])

                if 0.5 <= price < 5:
                    pennies.append(symbol)

            except:
                continue

        return pennies[:20]

    except:
        return []


# ==============================
# CRYPTO MOMENTUM
# ==============================

def get_top_crypto(limit=15):
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        data = safe_get(url)

        data = sorted(
            data,
            key=lambda x: float(x.get("quoteVolume", 0)),
            reverse=True
        )

        top = []

        for item in data:
            sym = item.get("symbol", "")
            if sym.endswith("USDT"):
                top.append(sym)

            if len(top) >= limit:
                break

        return top

    except:
        return []


# ==============================
# BUILD HYBRID UNIVERSE
# ==============================

def build_universe():
    global last_build, cached_universe

    if time.time() - last_build < 600 and cached_universe:
        return cached_universe

    most_active = get_most_active()
    gainers = get_top_gainers()
    penny = get_penny_breakouts()

    # Merge & deduplicate
    stocks = list(set(most_active + gainers + penny))

    # HARD LIMIT (Railway safety)
    stocks = stocks[:60]

    crypto = get_top_crypto(limit=15)

    cached_universe = (stocks, crypto)
    last_build = time.time()

    return cached_universe