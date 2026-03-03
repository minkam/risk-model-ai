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


def fetch_intraday(symbol):
    try:
        url = f"{BASE_URL}/time_series"
        params = {
            "symbol": symbol,
            "interval": "30min",
            "outputsize": 100,
            "apikey": API_KEY
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        if "values" not in data:
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

    except:
        return None


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

    prob = min(max(score * 4, 0), 99)
    return round(prob, 2)


def scan_market():
    global last_scan, cached_results

    if cached_results and time.time() - last_scan < 300:
        return cached_results

    stocks = get_top_movers()
    crypto = get_top_crypto()

    results = []

    for symbol in stocks[:20]:
        df = fetch_intraday(symbol)
        if df is None:
            continue

        prob = compute_score(df)
        if prob > 60:
            results.append({
                "symbol": symbol,
                "prob": prob,
                "price": round(df["close"].iloc[-1], 2)
            })

        time.sleep(0.5)  # protect free tier

    for symbol in crypto[:10]:
        df = fetch_intraday(symbol)
        if df is None:
            continue

        prob = compute_score(df)
        if prob > 60:
            results.append({
                "symbol": symbol,
                "prob": prob,
                "price": round(df["close"].iloc[-1], 2)
            })

        time.sleep(0.5)

    results = sorted(results, key=lambda x: x["prob"], reverse=True)

    cached_results = results[:10]
    last_scan = time.time()

    return cached_results


def generate_eod_report():
    stocks = get_top_movers()[:10]
    report = "📊 EOD TOP MOVERS\n\n"

    for symbol in stocks:
        df = fetch_intraday(symbol)
        if df is None:
            continue

        change = ((df["close"].iloc[-1] - df["close"].iloc[0]) / df["close"].iloc[0]) * 100
        report += f"{symbol} | {round(change,2)}%\n"

        time.sleep(0.3)

    return report


def generate_open_report():
    stocks = get_top_movers()[:10]
    report = "🔔 OPEN SNAPSHOT\n\n"

    for symbol in stocks:
        df = fetch_intraday(symbol)
        if df is None:
            continue

        change = ((df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2]) * 100
        report += f"{symbol} | {round(change,2)}%\n"

        time.sleep(0.3)

    return report