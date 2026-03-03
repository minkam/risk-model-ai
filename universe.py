import requests
import os

API_KEY = os.getenv("TWELVE_API_KEY")
BASE_URL = "https://api.twelvedata.com"

SYMBOLS = ["NVDA","TSLA","AMD","SMCI","META"]

def scan_market():

    results = []

    print("\nLight scan mode active...")

    for symbol in SYMBOLS:

        try:
            url = f"{BASE_URL}/quote"
            params = {
                "symbol": symbol,
                "apikey": API_KEY
            }

            r = requests.get(url, params=params)

            data = r.json()

            if "percent_change" not in data:
                continue

            change = float(data["percent_change"])
            price = float(data["close"])

            probability = min(abs(change) * 5, 95)

            if abs(change) > 1.5:
                results.append({
                    "symbol": symbol,
                    "prob": round(probability, 1),
                    "price": price,
                    "change": round(change,2)
                })

        except:
            continue

    print("Results:", results)

    return results


def generate_open_report():
    return "Open report disabled on free tier."

def generate_eod_report():
    return "EOD report disabled on free tier."