import yfinance as yf
import pandas as pd
import numpy as np

# ==============================
# STOCK UNIVERSE
# ==============================

STOCK_UNIVERSE = [
    # Mega Caps
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA",
    "AVGO","JPM","V","MA","UNH","HD","PG","XOM","LLY",

    # High Growth / Momentum
    "CRWD","ZS","SNOW","PLTR","COIN","SHOP","DDOG",
    "ROKU","NET","UPST","AFRM","DKNG",

    # Active / Volatile
    "AMC","GME","RIOT","MARA","SOFI","LCID","RIVN"
]

# ==============================
# CRYPTO UNIVERSE
# ==============================

CRYPTO_UNIVERSE = [
    "BTC-USD","ETH-USD","SOL-USD","XRP-USD","AVAX-USD",
    "LINK-USD","DOGE-USD","ADA-USD","DOT-USD",
    "ARB-USD","OP-USD","ATOM-USD"
]

# ==============================
# FEATURE ENGINE
# ==============================

def calculate_features(df):
    df["ema20"] = df["Close"].ewm(span=20).mean()
    df["ema50"] = df["Close"].ewm(span=50).mean()

    df["volume_avg"] = df["Volume"].rolling(20).mean()
    df["relative_volume"] = df["Volume"] / df["volume_avg"]

    df["momentum_7d"] = df["Close"].pct_change(7)

    return df

# ==============================
# STOCK SCANNER
# ==============================

def scan_stocks():
    results = []

    for symbol in STOCK_UNIVERSE:
        try:
            df = yf.download(symbol, period="6mo", progress=False)

            if df.empty or len(df) < 60:
                continue

            df = calculate_features(df)
            last = df.iloc[-1]

            # High probability long logic
            if (
                last["Close"] > last["ema20"] and
                last["ema20"] > last["ema50"] and
                last["relative_volume"] > 1.2 and
                last["momentum_7d"] > 0.03
            ):
                results.append({
                    "symbol": symbol,
                    "type": "STOCK",
                    "momentum": round(float(last["momentum_7d"]), 4),
                    "relative_volume": round(float(last["relative_volume"]), 2)
                })

        except:
            continue

    return sorted(results, key=lambda x: x["momentum"], reverse=True)

# ==============================
# CRYPTO SCANNER
# ==============================

def scan_crypto():
    results = []

    for symbol in CRYPTO_UNIVERSE:
        try:
            df = yf.download(symbol, period="6mo", progress=False)

            if df.empty or len(df) < 60:
                continue

            df = calculate_features(df)
            last = df.iloc[-1]

            if (
                last["Close"] > last["ema20"] and
                last["ema20"] > last["ema50"] and
                last["momentum_7d"] > 0.05
            ):
                results.append({
                    "symbol": symbol,
                    "type": "CRYPTO",
                    "momentum": round(float(last["momentum_7d"]), 4)
                })

        except:
            continue

    return sorted(results, key=lambda x: x["momentum"], reverse=True)

# ==============================
# MASTER SCAN
# ==============================

def scan_market():
    return {
        "stocks": scan_stocks(),
        "crypto": scan_crypto()
    }