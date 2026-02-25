import yfinance as yf
import pandas as pd
import numpy as np
import joblib


model = joblib.load("swing_model.pkl")


def get_universe():
    return [
        "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","AVGO","JPM",
        "V","MA","UNH","HD","PG","XOM","LLY","MRK","COST","ABBV",
        "PEP","ADBE","KO","CRM","CSCO","WMT","AMD","NFLX","TMO","ACN",
        "MCD","INTC","ORCL","CVX","ABT","LIN","TXN","DHR","PM","NEE",
        "ROKU","SHOP","PLTR","COIN","AFRM","UPST","CRWD","NET","DDOG",
        "ZS","SNOW","RIVN","LCID","SOFI","DKNG","MARA","RIOT","FUBO","PENN"
    ]


def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def run_scan():

    alerts = []

    for symbol in get_universe():

        try:
            df = yf.download(symbol, period="6mo", interval="1d", progress=False)

            if df.empty:
                continue

            df = flatten_columns(df)

            df["ma20"] = df["Close"].rolling(20).mean()
            df["ma50"] = df["Close"].rolling(50).mean()
            df["rsi"] = compute_rsi(df["Close"])
            df["atr"] = (df["High"] - df["Low"]).rolling(14).mean()

            df = df.dropna()

            latest = df.iloc[-1]

            # TREND FILTER
            if not (latest["Close"] > latest["ma20"] > latest["ma50"]):
                continue

            features = np.array([[
                latest["ma20"],
                latest["ma50"],
                latest["rsi"],
                latest["atr"]
            ]])

            prob = model.predict_proba(features)[0][1]

            if prob >= 0.75:
                alerts.append((symbol, prob))

        except:
            continue

    alerts.sort(key=lambda x: x[1], reverse=True)
    return alerts


if __name__ == "__main__":

    signals = run_scan()

    print("\n🚀 HIGH-PROBABILITY 3–5 DAY LONG ALERTS\n")

    if not signals:
        print("No strong setups right now.")
    else:
        for symbol, prob in signals:
            print(f"{symbol}  |  Probability: {round(prob,3)}")