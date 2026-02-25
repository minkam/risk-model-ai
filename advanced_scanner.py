import yfinance as yf
import pandas as pd
from datetime import datetime

# ===============================
# STOCK UNIVERSE
# ===============================

STOCKS = [
    "AAPL","MSFT","NVDA","TSLA","META","AMZN","GOOGL","AMD",
    "SPY","QQQ","PLTR","SMCI","COIN","NFLX","BA","DIS"
]

# ===============================
# CRYPTO UNIVERSE
# ===============================

CRYPTO = [
    "BTC-USD","ETH-USD","SOL-USD","XRP-USD",
    "DOGE-USD","AVAX-USD","ADA-USD","LINK-USD"
]

# ===============================
# SCAN FUNCTION
# ===============================

def scan_market(asset_type="all"):

    results = []

    tickers = []

    if asset_type == "stocks":
        tickers = STOCKS
    elif asset_type == "crypto":
        tickers = CRYPTO
    else:
        tickers = STOCKS + CRYPTO

    for ticker in tickers:
        try:
            df = yf.download(ticker, period="3mo", progress=False)

            if df.empty:
                continue

            df["50ma"] = df["Close"].rolling(50).mean()
            df["200ma"] = df["Close"].rolling(200).mean()

            latest = df.iloc[-1]

            trend = "Bullish" if latest["Close"] > latest["50ma"] else "Bearish"

            results.append({
                "ticker": ticker,
                "price": round(float(latest["Close"]), 2),
                "trend": trend
            })

        except:
            continue

    return results


# ===============================
# EOD REPORT
# ===============================

def generate_eod_report():

    spy = yf.download("SPY", period="5d", progress=False)
    btc = yf.download("BTC-USD", period="5d", progress=False)

    spy_change = round(((spy["Close"][-1] - spy["Close"][-2]) / spy["Close"][-2]) * 100, 2)
    btc_change = round(((btc["Close"][-1] - btc["Close"][-2]) / btc["Close"][-2]) * 100, 2)

    report = f"""
📊 END OF DAY REPORT

SPY: {spy_change}%
BTC: {btc_change}%

Market closed at {datetime.now().strftime('%I:%M %p')}
"""

    return report


# ===============================
# MARKET OPEN REPORT
# ===============================

def generate_open_report():

    spy = yf.download("SPY", period="5d", progress=False)
    btc = yf.download("BTC-USD", period="5d", progress=False)

    spy_change = round(((spy["Close"][-1] - spy["Close"][-2]) / spy["Close"][-2]) * 100, 2)
    btc_change = round(((btc["Close"][-1] - btc["Close"][-2]) / btc["Close"][-2]) * 100, 2)

    report = f"""
🔔 MARKET OPEN REPORT

SPY overnight: {spy_change}%
BTC overnight: {btc_change}%

Market open scan ready.
"""

    return report