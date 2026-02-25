import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# ===============================
# UNIVERSES
# ===============================

STOCKS = [
    "AAPL","MSFT","NVDA","TSLA","AMD","AMZN","META","NFLX",
    "AVGO","JPM","BAC","GS","COIN","XOM","PLTR","SMCI"
]

CRYPTO = [
    "BTC-USD","ETH-USD","SOL-USD","DOGE-USD",
    "XRP-USD","ADA-USD","LINK-USD","AVAX-USD"
]

# ===============================
# SAFE DOWNLOAD
# ===============================

def download_data(tickers):
    try:
        data = yf.download(
            tickers=tickers,
            period="5d",
            group_by="ticker",
            auto_adjust=True,
            threads=True
        )
        return data
    except:
        return None

# ===============================
# CALCULATE TOP GAINERS
# ===============================

def get_top_movers(tickers):

    data = download_data(tickers)
    if data is None:
        return []

    results = []

    for ticker in tickers:
        try:
            df = data[ticker].dropna()

            if len(df) < 2:
                continue

            close_today = float(df["Close"].iloc[-1])
            close_yesterday = float(df["Close"].iloc[-2])

            change_pct = ((close_today - close_yesterday) / close_yesterday) * 100

            results.append((ticker, round(change_pct,2), round(close_today,2)))

        except:
            continue

    results.sort(key=lambda x: x[1], reverse=True)

    return results[:5]

# ===============================
# SETUP SCANNER
# ===============================

def scan_market():

    stock_setups = []
    crypto_setups = []

    data = download_data(STOCKS + CRYPTO)
    if data is None:
        return {"stocks": [], "crypto": []}

    for ticker in STOCKS + CRYPTO:
        try:
            df = data[ticker].dropna()

            if len(df) < 20:
                continue

            close = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2])
            volume = float(df["Volume"].iloc[-1])
            avg_volume = float(df["Volume"].rolling(20).mean().iloc[-1])

            change = ((close - prev) / prev) * 100

            # Simple breakout condition
            if change > 2 and volume > avg_volume:

                risk = 0.01  # 1% risk model
                stop = close * 0.97
                position_size = round((100000 * risk) / (close - stop), 2)

                setup = {
                    "ticker": ticker,
                    "price": round(close,2),
                    "change": round(change,2),
                    "position_size": position_size,
                    "stop": round(stop,2)
                }

                if "-USD" in ticker:
                    crypto_setups.append(setup)
                else:
                    stock_setups.append(setup)

        except:
            continue

    return {
        "stocks": stock_setups,
        "crypto": crypto_setups
    }

# ===============================
# END OF DAY REPORT
# ===============================

def generate_eod_report():

    stock_movers = get_top_movers(STOCKS)
    crypto_movers = get_top_movers(CRYPTO)

    report = "📊 END OF DAY REPORT\n\n"

    report += "🔥 Top 5 Stock Gainers:\n"
    for t,c,p in stock_movers:
        report += f"{t} | {p}$ | {c}%\n"

    report += "\n🪙 Top 5 Crypto Gainers:\n"
    for t,c,p in crypto_movers:
        report += f"{t} | {p}$ | {c}%\n"

    return report

# ===============================
# MARKET OPEN REPORT
# ===============================

def generate_open_report():

    stock_movers = get_top_movers(STOCKS)
    crypto_movers = get_top_movers(CRYPTO)

    report = "🔔 MARKET OPEN REPORT\n\n"

    report += "🚀 Early Stock Momentum:\n"
    for t,c,p in stock_movers:
        report += f"{t} | {c}%\n"

    report += "\n🪙 Early Crypto Momentum:\n"
    for t,c,p in crypto_movers:
        report += f"{t} | {c}%\n"

    return report