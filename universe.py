import yfinance as yf
import pandas as pd
import numpy as np
import time
from universe import build_universe, get_top_crypto_usdt

last_scan = 0
cached_result = None


# ===============================
# Feature Engineering
# ===============================

def compute_features(df):
    df["return"] = df["Close"].pct_change()
    df["rvol"] = df["Volume"] / df["Volume"].rolling(20).mean()
    df["mom3"] = df["Close"].pct_change(3)
    df["mom7"] = df["Close"].pct_change(7)
    df.dropna(inplace=True)
    return df


def score_symbol(df):
    last = df.iloc[-1]

    score = (
        (last["mom7"] * 3) +
        (last["mom3"] * 2) +
        (last["rvol"] * 1)
    )

    probability = min(max(score * 5, 0), 99)

    return round(probability, 2)


# ===============================
# SAFE DOWNLOAD
# ===============================

def safe_download(symbol):
    try:
        df = yf.download(
            symbol,
            period="2mo",
            interval="1d",
            progress=False,
            threads=False,
            auto_adjust=True
        )
        return df
    except:
        return None


# ===============================
# MAIN SCANNER
# ===============================

def scan_market():
    global last_scan, cached_result

    if cached_result and time.time() - last_scan < 300:
        return cached_result

    universe = build_universe()["all"]
    crypto = get_top_crypto_usdt(15)

    results = []

    # Limit to prevent rate limits
    universe = universe[:60]
    crypto = crypto[:10]

    # Scan Stocks
    for symbol in universe:
        df = safe_download(symbol)
        if df is None or df.empty or len(df) < 30:
            continue

        df = compute_features(df)
        if df.empty:
            continue

        prob = score_symbol(df)

        if prob > 65:
            results.append({
                "symbol": symbol,
                "prob": prob,
                "price": round(df["Close"].iloc[-1], 2)
            })

        time.sleep(0.25)  # critical to avoid rate limit

    # Scan Crypto
    for symbol in crypto:
        df = safe_download(symbol)
        if df is None or df.empty or len(df) < 30:
            continue

        df = compute_features(df)
        if df.empty:
            continue

        prob = score_symbol(df)

        if prob > 65:
            results.append({
                "symbol": symbol,
                "prob": prob,
                "price": round(df["Close"].iloc[-1], 2)
            })

        time.sleep(0.25)

    results = sorted(results, key=lambda x: x["prob"], reverse=True)

    cached_result = results[:12]
    last_scan = time.time()

    return cached_result