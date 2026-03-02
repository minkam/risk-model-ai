import yfinance as yf
import requests
import time

BASE_STOCKS = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA",
    "AMD","SHOP","PLTR","CRWD","SNOW","DDOG","COIN",
    "ZS","ROKU","UPST","NET","FUBO","RIOT","MARA",
    "SPY","QQQ","IWM","DIA"
]

PENNY_CANDIDATES = [
    "SNDL","CLOV","ATER","GPRO","TLRY","AMC","SOFI",
    "NKLA","MULN"
]

last_universe_build = 0
cached_universe = None


# ==============================
# PENNY FILTER (BATCHED)
# ==============================

def get_penny_stocks():
    try:
        data = yf.download(
            PENNY_CANDIDATES,
            period="5d",
            interval="1d",
            group_by="ticker",
            progress=False,
            threads=True
        )

        valid = []

        for symbol in PENNY_CANDIDATES:
            try:
                df = data[symbol]
                if df.empty:
                    continue

                last = float(df["Close"].iloc[-1])

                if 0.5 <= last < 5:
                    valid.append(symbol)

            except:
                continue

        return valid

    except:
        return []


# ==============================
# CRYPTO FILTER (LIMITED)
# ==============================

def get_top_crypto(limit=15):
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        data = requests.get(url, timeout=5).json()

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
# BUILD UNIVERSE (CACHED)
# ==============================

def build_universe():
    global last_universe_build, cached_universe

    # Cache for 10 minutes
    if time.time() - last_universe_build < 600 and cached_universe:
        return cached_universe

    penny = get_penny_stocks()
    stocks = list(set(BASE_STOCKS + penny))

    crypto = get_top_crypto(limit=15)

    cached_universe = (stocks, crypto)
    last_universe_build = time.time()

    return cached_universe