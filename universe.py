import requests

def get_top_gainers(limit=30):
    try:
        url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
        params = {"scrIds": "day_gainers", "count": limit}
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        quotes = data["finance"]["result"][0]["quotes"]
        return [q["symbol"] for q in quotes]
    except:
        return []

def get_most_active(limit=30):
    try:
        url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
        params = {"scrIds": "most_actives", "count": limit}
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        quotes = data["finance"]["result"][0]["quotes"]
        return [q["symbol"] for q in quotes]
    except:
        return []

def build_universe():
    gainers = get_top_gainers()
    active = get_most_active()

    symbols = list(set(gainers + active))

    # fallback if Yahoo fails
    if not symbols:
        symbols = ["AAPL", "MSFT", "NVDA", "TSLA", "AMD", "META"]

    return symbols[:40]