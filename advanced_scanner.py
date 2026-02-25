import yfinance as yf
import pandas as pd
import numpy as np

# --- STOCK UNIVERSE ---
STOCKS = [
    "AAPL","MSFT","NVDA","AMZN","META","TSLA","AMD","NFLX","GOOGL",
    "SHOP","COIN","PLTR","CRWD","SNOW","ZS","DDOG","ROKU"
]

# --- CRYPTO UNIVERSE ---
CRYPTO = [
    "BTC-USD","ETH-USD","SOL-USD","BNB-USD","XRP-USD",
    "DOGE-USD","ADA-USD","AVAX-USD","LINK-USD"
]


def calculate_features(df):
    df["sma20"] = df["Close"].rolling(20).mean()
    df["sma50"] = df["Close"].rolling(50).mean()
    df["rsi"] = 100 - (100 / (1 + df["Close"].pct_change().rolling(14).mean()))
    df["volume_avg"] = df["Volume"].rolling(20).mean()

    df["relative_volume"] = df["Volume"] / df["volume_avg"]

    df["momentum_5"] = df["Close"].pct_change(5)
    df["momentum_7"] = df["Close"].pct_change(7)

    return df


def score_asset(df):
    latest = df.iloc[-1]

    score = 0

    if latest["Close"] > latest["sma20"]:
        score += 1
    if latest["Close"] > latest["sma50"]:
        score += 1
    if latest["momentum_5"] > 0:
        score += 1
    if latest["relative_volume"] > 1.2:
        score += 1

    return score


def scan_list(symbols):
    results = []

    for symbol in symbols:
        try:
            df = yf.download(symbol, period="6mo", progress=False)

            if df.empty:
                continue

            df = calculate_features(df)
            score = score_asset(df)

            results.append({
                "symbol": symbol,
                "score": score,
                "price": round(df["Close"].iloc[-1], 2)
            })

        except:
            continue

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    return results


def scan_market(asset_type="all"):

    if asset_type == "stocks":
        return scan_list(STOCKS)

    if asset_type == "crypto":
        return scan_list(CRYPTO)

    stocks = scan_list(STOCKS)
    crypto = scan_list(CRYPTO)

    return {
        "stocks": stocks,
        "crypto": crypto
    }