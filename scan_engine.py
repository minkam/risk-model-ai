import yfinance as yf
import numpy as np
import time
from universe import build_universe

# Cache control
last_scan_time = 0
cached_results = None


# ==============================
# FEATURE ENGINE
# ==============================

def calculate_features(df):
    df["return"] = df["Close"].pct_change()
    df["sma20"] = df["Close"].rolling(20).mean()
    df["sma50"] = df["Close"].rolling(50).mean()
    df["volume_avg"] = df["Volume"].rolling(20).mean()
    df["relative_volume"] = df["Volume"] / df["volume_avg"]
    df["momentum_3d"] = df["Close"].pct_change(3)
    df["momentum_7d"] = df["Close"].pct_change(7)
    df["volatility"] = df["return"].rolling(10).std()
    df.dropna(inplace=True)
    return df


# ==============================
# AI PROBABILITY MODEL
# ==============================

def probability_model(last):

    score = 0

    # Momentum weighting
    score += last["momentum_7d"] * 4
    score += last["momentum_3d"] * 3

    # Volume expansion
    score += (last["relative_volume"] - 1) * 2

    # Trend confirmation
    if last["Close"] > last["sma20"]:
        score += 1
    if last["Close"] > last["sma50"]:
        score += 1

    # Volatility boost
    score += last["volatility"] * 2

    # Sigmoid to convert to probability
    probability = 1 / (1 + np.exp(-score))

    return round(float(probability), 3)


# ==============================
# MAIN SCANNER
# ==============================

def scan_market():
    global last_scan_time, cached_results

    # 5 minute cache (Railway safe)
    if time.time() - last_scan_time < 300 and cached_results:
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

            if df.empty or len(df) < 60:
                continue

            df = calculate_features(df)

            if df.empty:
                continue

            last = df.iloc[-1]

            prob = probability_model(last)

            entry = float(last["Close"])
            stop = entry * 0.95
            target = entry * 1.12

            results.append({
                "symbol": symbol,
                "prob": prob,
                "entry": round(entry, 2),
                "stop": round(stop, 2),
                "target": round(target, 2),
            })

        except:
            continue

    # Rank by AI probability
    results.sort(key=lambda x: x["prob"], reverse=True)

    # Always return top 10 (even in weak market)
    final_results = results[:10]

    cached_results = final_results
    last_scan_time = time.time()

    return final_results