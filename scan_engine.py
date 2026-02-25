import yfinance as yf
import pandas as pd
import numpy as np

# ==============================
# STOCK + CRYPTO UNIVERSE
# ==============================

STOCK_UNIVERSE = [
    "AAPL","MSFT","NVDA","TSLA","META","AMZN","GOOGL","AMD",
    "PLTR","COIN","SHOP","CRWD","SNOW","ROKU","ZS","DDOG",
    "NFLX","PANW","ADBE","INTC","BA","JPM","GS","XOM"
]

CRYPTO_UNIVERSE = [
    "BTC-USD","ETH-USD","SOL-USD","AVAX-USD",
    "DOGE-USD","XRP-USD","ADA-USD","LINK-USD"
]

# ==============================
# FEATURE ENGINE
# ==============================

def calculate_features(df):
    df["return"] = df["Close"].pct_change()
    df["volume_avg"] = df["Volume"].rolling(20).mean()
    df["relative_volume"] = df["Volume"] / df["volume_avg"]
    df["momentum_7d"] = df["Close"].pct_change(7)
    df["momentum_3d"] = df["Close"].pct_change(3)
    df.dropna(inplace=True)
    return df

# ==============================
# SINGLE SYMBOL SCAN
# ==============================

def scan_symbol(symbol):
    try:
        df = yf.download(symbol, period="6mo", progress=False)
        if df.empty:
            return None

        df = calculate_features(df)
        last = df.iloc[-1]

        score = (
            (last["momentum_7d"] * 2) +
            (last["momentum_3d"] * 1.5) +
            (last["relative_volume"] * 0.5)
        )

        return {
            "symbol": symbol,
            "price": round(last["Close"], 2),
            "score": round(float(score), 3)
        }

    except Exception:
        return None

# ==============================
# MAIN SCANNER
# ==============================

def scan_market():
    stock_results = []
    crypto_results = []

    for symbol in STOCK_UNIVERSE:
        result = scan_symbol(symbol)
        if result:
            stock_results.append(result)

    for symbol in CRYPTO_UNIVERSE:
        result = scan_symbol(symbol)
        if result:
            crypto_results.append(result)

    stock_results = sorted(stock_results, key=lambda x: x["score"], reverse=True)
    crypto_results = sorted(crypto_results, key=lambda x: x["score"], reverse=True)

    return {
        "stocks": stock_results,
        "crypto": crypto_results
    }