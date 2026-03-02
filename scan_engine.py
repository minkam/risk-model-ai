
import yfinance as yf
import numpy as np
import time
from universe import build_universe

last_scan = 0
cached_results = None


def calculate_features(df):
    df["return"] = df["Close"].pct_change()
    df["sma20"] = df["Close"].rolling(20).mean()
    df["volume_avg"] = df["Volume"].rolling(20).mean()
    df["relative_volume"] = df["Volume"] / df["volume_avg"]
    df["momentum_7d"] = df["Close"].pct_change(7)
    df.dropna(inplace=True)
    return df


def score_symbol(df):
    last = df.iloc[-1]
    score = (
        (last["momentum_7d"] * 2) +
        (last["relative_volume"] * 0.5)
    )
    return round(float(score), 3)


def scan_market():
    global last_scan, cached_results

    if time.time() - last_scan < 300 and cached_results:
        return cached_results

    stocks, crypto = build_universe()
    symbols = stocks + crypto

    if not symbols:
        return []

    try:
        data = yf.download(
            symbols,
            period="3mo",
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True
        )
    except:
        return []

    results = []

    for symbol in symbols:
        try:
            df = data[symbol].copy()
            if df.empty or len(df) < 30:
                continue

            df = calculate_features(df)
            score = score_symbol(df)

            if score > 0.5:
                price = round(float(df["Close"].iloc[-1]), 2)
                stop = round(price * 0.95, 2)
                target = round(price * 1.10, 2)

                results.append({
                    "symbol": symbol,
                    "score": score,
                    "entry": price,
                    "stop": stop,
                    "target": target
                })

        except:
            continue

    results.sort(key=lambda x: x["score"], reverse=True)

    final = results[:10]

    cached_results = final
    last_scan = time.time()

    return final