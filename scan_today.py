import numpy as np
import joblib
import yfinance as yf
import time
from universe import build_universe

MODEL_PATH = "swing_model.pkl"
model = joblib.load(MODEL_PATH)

last_scan_time = 0
cached_results = None


# ==============================
# FEATURE ENGINE
# ==============================

def prepare_features(df):
    df["return"] = df["Close"].pct_change()
    df["sma20"] = df["Close"].rolling(20).mean()
    df["sma50"] = df["Close"].rolling(50).mean()
    df["volatility"] = df["return"].rolling(10).std()
    df.dropna(inplace=True)
    return df


# ==============================
# BATCH DOWNLOAD
# ==============================

def batch_download(symbols):
    data = yf.download(
        symbols,
        period="3mo",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        progress=False,
        threads=True
    )
    return data


# ==============================
# PROCESS SYMBOL
# ==============================

def process_symbol(symbol, data):
    try:
        df = data[symbol].copy()
        if df.empty or len(df) < 60:
            return None

        df = prepare_features(df)
        if df.empty:
            return None

        latest = df.iloc[-1]

        X = np.array([[ 
            float(latest["return"]),
            float(latest["Close"] / latest["sma20"]),
            float(latest["Close"] / latest["sma50"]),
            float(latest["volatility"])
        ]])

        prob = float(model.predict_proba(X)[0][1])

        if prob < 0.85:
            return None

        entry = float(latest["Close"])
        stop = entry * 0.95
        target = entry * 1.10

        return {
            "symbol": symbol,
            "prob": round(prob, 3),
            "entry": round(entry, 2),
            "stop": round(stop, 2),
            "target": round(target, 2),
        }

    except Exception:
        return None


# ==============================
# MAIN SCANNER
# ==============================

def scan_market():
    global last_scan_time, cached_results

    # 5 minute cache
    if time.time() - last_scan_time < 300 and cached_results:
        return cached_results

    stocks, crypto = build_universe()

    # Hard limit universe to protect Railway
    stocks = stocks[:25]
    crypto = crypto[:15]

    all_symbols = stocks + crypto

    data = batch_download(all_symbols)

    results = []

    for symbol in all_symbols:
        r = process_symbol(symbol, data)
        if r:
            results.append(r)

    results.sort(key=lambda x: x["prob"], reverse=True)

    final = results[:12]

    cached_results = final
    last_scan_time = time.time()

    return final