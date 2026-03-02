import requests
import yfinance as yf

def get_top_gainers(limit=40):
    url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
    params = {"scrIds": "day_gainers", "count": limit}
    try:
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        quotes = data["finance"]["result"][0]["quotes"]
        return [q["symbol"] for q in quotes]
    except:
        return []

def get_most_active(limit=40):
    url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
    params = {"scrIds": "most_actives", "count": limit}
    try:
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        quotes = data["finance"]["result"][0]["quotes"]
        return [q["symbol"] for q in quotes]
    except:
        return []

def get_top_crypto(limit=25):
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        data = requests.get(url, timeout=5).json()
        data = sorted(data, key=lambda x: float(x.get("quoteVolume", 0)), reverse=True)
        return [x["symbol"] for x in data if x["symbol"].endswith("USDT")][:limit]
    except:
        return []

def build_universe():
    gainers = get_top_gainers()
    active = get_most_active()
    stocks = list(set(gainers + active))
    crypto = get_top_crypto()
    return stocks[:60], crypto