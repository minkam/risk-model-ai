import yfinance as yf
import pandas as pd
import numpy as np
import time

STOCK_UNIVERSE = [
    "AAPL","MSFT","NVDA","TSLA","META","AMZN","GOOGL","AMD",
    "PLTR","COIN","SHOP","CRWD","SNOW","ROKU","ZS","DDOG",
    "NFLX","PANW","ADBE","INTC","BA","JPM","GS","XOM"
]

CRYPTO_UNIVERSE = [
    "BTC-USD","ETH-USD","SOL-USD","AVAX-USD",
    "DOGE-USD","XRP-USD","ADA-USD","LINK-USD"
]

last_scan_time = 0
cached_result = None


# ==============================
# FEATURE ENGINE
# ==============================

def calculate_features(df):
    df["return"] = df["Close"].pct_change()
    df["volume_avg"] = df["Volume"].rolling(20).mean()
    df["relative_volume"] = df["Volume"] / df["volume_avg"]
    df["momentum_7d"] = df["Close"].pct_change(7)
    df["momentum_3d"] = df["Close"].pct_change(3)
    return df


# ==============================
# BATCH SCAN
# ==============================

def batch_scan(symbols):
    data = yf.download(
        symbols,
        period="3mo",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        progress=False,
        threads=True
    )

    results = []

    for symbol in symbols:
        try:
            df = data[symbol].copy()
            if df.empty:
                continue

            df = calculate_features(df)
            df.dropna(inplace=True)

            last = df.iloc[-1]

            score = (
                (last["momentum_7d"] * 2) +
                (last["momentum_3d"] * 1.5) +
                (last["relative_volume"] * 0.5)
            )

            results.append({
                "symbol": symbol,
                "price": round(float(last["Close"]), 2),
                "score": round(float(score), 3)
            })

        except Exception:
            continue

    return sorted(results, key=lambda x: x["score"], reverse=True)


# ==============================
# MAIN SCANNER
# ==============================

def scan_market():
    global last_scan_time, cached_result

    # Cache for 5 minutes
    if time.time() - last_scan_time < 300 and cached_result:
        return cached_result

    stock_results = batch_scan(STOCK_UNIVERSE)
    crypto_results = batch_scan(CRYPTO_UNIVERSE)

    result = {
        "stocks": stock_results[:5],
        "crypto": crypto_results[:5]
    }

    cached_result = result
    last_scan_time = time.time()

    return result