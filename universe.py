import requests
import os

API_KEY = os.getenv("TWELVE_API_KEY")
BASE_URL = "https://api.twelvedata.com"

# Strong liquid stocks only
BASE_STOCKS = [
    "NVDA","TSLA","AMD","AAPL","MSFT",
    "META","AMZN","SMCI","COIN","NFLX",
    "PLTR","RIVN","SOFI","INTC","BA",
    "DIS","UBER","NIO","PYPL","SHOP"
]

BASE_CRYPTO = [
    "BTC/USD",
    "ETH/USD",
    "SOL/USD",
    "DOGE/USD",
    "XRP/USD"
]


def get_top_movers():

    movers = []

    print("\nFetching daily data for base stocks...")

    for symbol in BASE_STOCKS:

        try:
            url = f"{BASE_URL}/quote"
            params = {
                "symbol": symbol,
                "apikey": API_KEY
            }

            r = requests.get(url, params=params, timeout=10)

            if r.status_code != 200:
                continue

            data = r.json()

            if "percent_change" not in data:
                continue

            change = abs(float(data["percent_change"]))

            movers.append((symbol, change))

        except:
            continue

    # sort by biggest % move
    movers.sort(key=lambda x: x[1], reverse=True)

    final = [x[0] for x in movers[:6]]

    print("Top movers:", final)

    return final


def get_top_crypto():
    return BASE_CRYPTO