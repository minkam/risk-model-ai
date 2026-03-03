import requests
import os
import time
import pandas as pd
import numpy as np
from universe import get_top_movers, get_top_crypto

API_KEY = os.getenv("TWELVE_API_KEY")
BASE_URL = "https://api.twelvedata.com"

last_scan = 0
cached_results = None


# ===============================
# FETCH INTRADAY DATA (DIAGNOSTIC)
# ===============================

def fetch_intraday(symbol):
    try:
        url = f"{BASE_URL}/time_series"
        params = {
            "symbol": symbol,
            "interval": "30min",
            "outputsize": 50,
            "apikey": API_KEY
        }

        r = requests.get(url, params=params, timeout=10)

        print(f"\n--- Fetching {symbol} ---")
        print("Status Code:", r.status_code)

        data = r.json()
        print("Response:", data)

        if "values" not in data:
            print(f"No candle data returned for {symbol}")
            return None

        df = pd.DataFrame(data["values"])

        df = df.astype({
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": float
        })

        df = df.sort_values("datetime")

        return df

    except Exception as e:
        print("Error fetching:", symbol, e)
        return None


# ===============================
# SCORING
# ===============================

def compute_score(df):

    df["return"] = df["close"].pct_change()
    df["mom3"] = df["close"].pct_change(3)
    df["mom7"] = df["close"].pct_change(7)
    df["rvol"] = df["volume"] / df["volume"].rolling(10).mean()

    df.dropna(inplace=True)

    if df.empty:
        return 0

    last = df.iloc[-1]

    score = (
        (last["mom7"] * 3) +
        (last["mom3"] * 2) +
        (last["rvol"] * 1)
    )

    probability = min(max(score * 4, 0), 99)

    return round(probability, 2)


# ===============================
# MAIN SCAN (REDUCED SIZE)
# ===============================

def scan_market():
    global last_scan, cached_results

    stocks = get_top_movers()[:3]
    crypto = get_top_crypto()[:1]

    print("\nStocks to scan:", stocks)
    print("Crypto to scan:", crypto)

    results = []

    for symbol in stocks:
        df = fetch_intraday(symbol)
        if df is None:
            continue

        prob = compute_score(df)
        print("Probability:", prob)

        if prob > 50:
            results.append({
                "symbol": symbol,
                "prob": prob,
                "price": round(df["close"].iloc[-1], 2)
            })

        time.sleep(1)

    for symbol in crypto:
        df = fetch_intraday(symbol)
        if df is None:
            continue

        prob = compute_score(df)
        print("Probability:", prob)

        if prob > 50:
            results.append({
                "symbol": symbol,
                "prob": prob,
                "price": round(df["close"].iloc[-1], 2)
            })

        time.sleep(1)

    print("\nFinal Results:", results)

    return results


# ===============================
# SIMPLE REPORTS (DIAGNOSTIC)
# ===============================

def generate_eod_report():
    return "EOD diagnostic mode active. Check logs."

def generate_open_report():
    return "Open diagnostic mode active. Check logs."