import requests
import os

API_KEY = os.getenv("TWELVE_API_KEY")
BASE_URL = "https://api.twelvedata.com"


def get_top_movers():
    try:
        url = f"{BASE_URL}/stocks?exchange=NASDAQ&apikey={API_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()

        symbols = []
        for item in data.get("data", []):
            symbols.append(item["symbol"])

        return symbols[:50]  # limit for free tier
    except:
        return []


def get_top_crypto(limit=10):
    try:
        url = f"{BASE_URL}/cryptocurrencies?apikey={API_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()

        symbols = []
        for item in data.get("data", []):
            if item["currency_quote"] == "USD":
                symbols.append(item["symbol"])

        return symbols[:limit]
    except:
        return []