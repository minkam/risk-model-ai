import yfinance as yf
import pandas as pd
import datetime


# ================================
# STOCK SCAN
# ================================

def scan_stocks():
    tickers = ["AAPL", "TSLA", "NVDA", "AMD", "MSFT", "META", "AMZN", "SPY"]

    results = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, period="3mo", progress=False)

            if df.empty or len(df) < 20:
                continue

            df["SMA20"] = df["Close"].rolling(20).mean()
            df["Volume_Avg"] = df["Volume"].rolling(20).mean()

            last = df.iloc[-1]
            prev = df.iloc[-2]

            relative_volume = last["Volume"] / last["Volume_Avg"] if last["Volume_Avg"] != 0 else 0
            momentum = (last["Close"] - prev["Close"]) / prev["Close"] * 100

            if relative_volume > 1.5 and momentum > 1:
                results.append({
                    "ticker": ticker,
                    "price": round(last["Close"], 2),
                    "rv": round(relative_volume, 2),
                    "momentum": round(momentum, 2)
                })

        except:
            continue

    return results


# ================================
# CRYPTO SCAN
# ================================

def scan_crypto():
    cryptos = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "DOGE-USD"]

    results = []

    for coin in cryptos:
        try:
            df = yf.download(coin, period="3mo", progress=False)

            if df.empty or len(df) < 20:
                continue

            df["Volume_Avg"] = df["Volume"].rolling(20).mean()

            last = df.iloc[-1]
            prev = df.iloc[-2]

            relative_volume = last["Volume"] / last["Volume_Avg"] if last["Volume_Avg"] != 0 else 0
            momentum = (last["Close"] - prev["Close"]) / prev["Close"] * 100

            if relative_volume > 1.5 and momentum > 2:
                results.append({
                    "ticker": coin,
                    "price": round(last["Close"], 2),
                    "rv": round(relative_volume, 2),
                    "momentum": round(momentum, 2)
                })

        except:
            continue

    return results


# ================================
# EOD REPORT (FIXED)
# ================================

def generate_eod_report():
    spy = yf.download("SPY", period="5d", progress=False)

    if spy.empty or len(spy) < 2:
        return "Not enough SPY data."

    close_today = spy["Close"].iloc[-1]
    close_yesterday = spy["Close"].iloc[-2]

    spy_change = round(((close_today - close_yesterday) / close_yesterday) * 100, 2)

    return f"""
📊 END OF DAY REPORT

SPY Change: {spy_change}%

Market Bias:
{"Bullish" if spy_change > 0 else "Bearish"}

Volatility: Moderate
Tomorrow Focus: Watch pre-market volume
"""


# ================================
# MARKET OPEN REPORT (FIXED)
# ================================

def generate_open_report():
    spy = yf.download("SPY", period="5d", progress=False)

    if spy.empty or len(spy) < 2:
        return "Not enough SPY data."

    close_today = spy["Close"].iloc[-1]
    close_yesterday = spy["Close"].iloc[-2]

    spy_change = round(((close_today - close_yesterday) / close_yesterday) * 100, 2)

    return f"""
🔔 MARKET OPEN REPORT

Overnight SPY Change: {spy_change}%

Opening Bias:
{"Bullish Open" if spy_change > 0 else "Weak Open"}

Plan:
• Watch first 15min range
• Monitor relative volume spikes
"""