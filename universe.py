import requests
import os

API_KEY = os.getenv("TWELVE_API_KEY")
BASE_URL = "https://api.twelvedata.com"


def get_top_movers():

    print("\nFetching REAL movers...")

    url = f"{BASE_URL}/market_movers"

    params = {
        "apikey": API_KEY
    }

    r = requests.get(url, params=params)
    data = r.json()

    gainers = []
    losers = []

    if "gainers" in data:
        gainers = [x["symbol"] for x in data["gainers"][:10]]

    if "losers" in data:
        losers = [x["symbol"] for x in data["losers"][:10]]

    movers = list(set(gainers + losers))

    print("Movers Found:", movers)

    return movers


def get_top_crypto():

    url = f"{BASE_URL}/cryptocurrencies"
    params = {"apikey": API_KEY}

    r = requests.get(url, params=params)
    data = r.json()

    if "data" not in data:
        return []

    top = [x["symbol"] for x in data["data"][:5]]

    print("Crypto Found:", top)

    return top