import yfinance as yf
import pandas as pd
import numpy as np
import time
from universe import build_universe

PORTFOLIO_SIZE = 100000
RISK_PER_TRADE = 0.01

last_scan_time = 0
cached_results = None


def calculate_features(df):
    df["return"] = df["Close"].pct_change()
    df["sma20"] = df["Close"].rolling(20).mean()
    df["sma50"] = df["Close"].rolling(50).mean()
    df["vol_avg"] = df["Volume"].rolling(20).mean()
    df["rel_vol"] = df["Volume"] / df["vol_avg"]
    df["mom7"] = df["Close"].pct_change(7)
    df["mom3"] = df["Close"].pct_change(3)
    df.dropna(inplace=True)
    return df


def score_symbol(df):
    last = df.iloc[-1]
    score = (
        (last["mom7"] * 2) +
        (last["mom3"] * 1.5) +
        (last["rel_vol"] * 1) +
        (last["return"] * 2)
    )

    if last["Close"] > last["sma20"]:
        score += 0.5
    if last["sma20"] > last["sma50"]:
        score += 0.5

    return float(score)


def position_size(entry, stop):
    risk_amount = PORTFOLIO_SIZE * RISK_PER_TRADE
    risk_per_share = entry - stop
    if risk_per_share <= 0:
        return 0
    return round(risk_amount / risk_per_share, 2)


def scan_market():
    global last_scan_time, cached_results

    if time.time() - last_scan_time < 300 and cached_results:
        return cached_results

    symbols = build_universe()

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
            if symbol not in data:
                continue

            df = data[symbol].copy()

            if df.empty or len(df) < 60:
                continue

            df = calculate_features(df)

            if df.empty:
                continue

            score = score_symbol(df)

            if score < 1.5:
                continue

            entry = float(df["Close"].iloc[-1])
            stop = entry * 0.95
            target = entry * 1.12

            results.append({
                "symbol": symbol,
                "entry": round(entry, 2),
                "stop": round(stop, 2),
                "target": round(target, 2),
                "size": position_size(entry, stop),
                "score": round(score, 3)
            })

        except:
            continue

    results = sorted(results, key=lambda x: x["score"], reverse=True)[:10]

    cached_results = results
    last_scan_time = time.time()

    return results