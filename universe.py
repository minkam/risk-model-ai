import yfinance as yf
import requests

# ---- STOCKS ----
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

def get_penny_stocks():
    valid = []
    for symbol in PENNY_CANDIDATES:
        try:
            df = yf.download(symbol, period="5d", progress=False)
            if not df.empty:
                last = float(df["Close"].iloc[-1])
                if 0.5 <= last < 5:
                    valid.append(symbol)
        except:
            continue
    return valid

# ---- CRYPTO (AUTO) ----
# Uses Binance 24hr volume list, returns top ~50 USDT pairs
def get_top_crypto(limit=50):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    data = requests.get(url, timeout=15).json()

    # Sort by quoteVolume desc
    data = sorted(data, key=lambda x: float(x.get("quoteVolume", 0)), reverse=True)

    top = []
    for item in data:
        sym = item.get("symbol", "")
        if sym.endswith("USDT"):
            top.append(sym)
        if len(top) >= limit:
            break
    return top

def build_universe():
    stocks = list(set(BASE_STOCKS + get_penny_stocks()))
    crypto = get_top_crypto(limit=50)
    return stocks, crypto