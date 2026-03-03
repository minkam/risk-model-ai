# scan_engine.py

import time
import math
import yfinance as yf
import pandas as pd
from universe import build_universe, get_top_crypto_usdt

_last_scan = 0
_cached = None


# ==========================
# Probability Mapping
# ==========================

def prob_from_score(score):
    x = (score - 70) / 6
    p = 1 / (1 + math.exp(-x))
    return round(float(p), 3)


# ==========================
# Feature Scoring
# ==========================

def score_symbol(df, price):
    if len(df) < 50:
        return 0, None

    close = df["Close"]
    volume = df["Volume"]

    r1 = close.pct_change(1)
    r3 = close.pct_change(3)
    r7 = close.pct_change(7)

    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()

    vol_avg = volume.rolling(20).mean()
    rel_vol = volume / vol_avg

    breakout_level = close.rolling(10).max().shift(1)

    df_feat = pd.DataFrame({
        "r3": r3,
        "r7": r7,
        "trend20": close / sma20,
        "trend50": close / sma50,
        "rel_vol": rel_vol,
        "breakout": close > breakout_level,
    }).dropna()

    if df_feat.empty:
        return 0, None

    last = df_feat.iloc[-1]

    momentum = (last["r7"] * 100) * 1.2 + (last["r3"] * 100)
    volume_score = min(float(last["rel_vol"]), 5) * 8
    trend_score = ((last["trend20"] - 1) * 100) * 1.2
    breakout_score = 15 if last["breakout"] else 0

    raw_score = 50 + momentum + volume_score + trend_score + breakout_score

    # Sub-$1 penalty multiplier
    if price < 1:
        raw_score *= 0.85
    elif price > 10:
        raw_score *= 0.95

    score = max(0, min(100, raw_score))

    setup_type = None
    if last["breakout"] and last["rel_vol"] > 1.8:
        setup_type = "BREAKOUT"
    elif last["trend20"] > 1 and last["trend50"] > 1 and last["rel_vol"] > 1.2:
        setup_type = "CONTINUATION"

    return round(score, 1), setup_type


# ==========================
# Safe Batch Download
# ==========================

def batch_download(symbols):
    results = {}
    for i in range(0, len(symbols), 15):
        batch = symbols[i:i+15]
        try:
            data = yf.download(
                batch,
                period="5d",
                interval="30m",
                group_by="ticker",
                auto_adjust=True,
                progress=False,
                threads=True
            )
        except Exception:
            continue

        if isinstance(data.columns, pd.Index):
            results[batch[0]] = data
        else:
            for sym in batch:
                try:
                    df = data[sym]
                    if not df.empty:
                        results[sym] = df
                except:
                    continue
    return results


# ==========================
# Main Scanner
# ==========================

def scan_market():
    global _last_scan, _cached

    if _cached and time.time() - _last_scan < 300:
        return _cached

    universe = build_universe()
    stocks = universe["all"][:300]

    crypto_pairs = get_top_crypto_usdt(limit=20)
    crypto_symbols = [s.replace("USDT", "-USD") for s in crypto_pairs]

    stock_data = batch_download(stocks)
    crypto_data = batch_download(crypto_symbols)

    setups = []

    def process_symbol(symbol, df, bucket):
        try:
            price = float(df["Close"].iloc[-1])
            score, setup_type = score_symbol(df, price)

            if score < 70 or not setup_type:
                return

            entry = round(price, 2)
            stop = round(price * 0.95, 2)
            target = round(price * 1.10, 2)

            setups.append({
                "symbol": symbol,
                "bucket": bucket,
                "type": setup_type,
                "price": entry,
                "score": score,
                "prob": prob_from_score(score),
                "entry": entry,
                "stop": stop,
                "target": target
            })

        except:
            return

    for sym, df in stock_data.items():
        process_symbol(sym, df, "STOCK")

    for sym, df in crypto_data.items():
        process_symbol(sym, df, "CRYPTO")

    setups.sort(key=lambda x: x["score"], reverse=True)

    result = {
        "setups": setups[:15],
        "meta": {
            "stocks_scanned": len(stock_data),
            "crypto_scanned": len(crypto_data),
            "found": len(setups)
        }
    }

    _cached = result
    _last_scan = time.time()

    return result