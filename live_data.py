import yfinance as yf
import pandas as pd


def get_5m_data(symbol):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="1d", interval="5m")
    if df is None or df.empty:
        return None
    return df


def get_daily_data(symbol, days=120):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=f"{days}d", interval="1d")
    if df is None or df.empty:
        return None
    return df