import yfinance as yf
import pandas as pd
import numpy as np
from time import sleep


# -----------------------------
# CORE UNIVERSE
# -----------------------------
def get_universe():
    return [
        # Large Caps
        "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","AVGO","JPM","V","MA",
        "UNH","HD","PG","XOM","LLY","MRK","COST","ABBV","PEP","ADBE","KO","CRM",
        "CSCO","WMT","AMD","NFLX","TMO","ACN","MCD","INTC","ORCL","CVX","ABT",
        "LIN","TXN","DHR","PM","NEE","HON","IBM","AMGN","QCOM","LOW","RTX",
        "SPGI","CAT","GS","BKNG","NOW","ISRG","BLK","MDT","BA","PLD","SYK",
        "LMT","DE","CB","SCHW","CI","GE","VRTX","TMUS","PANW","ADI","ELV",
        "ZTS","MO","PFE","GILD","MU","SNPS","CL","SHW","BDX","TGT","FIS",
        "SO","ITW","MMC","ICE","APD","USB","EOG","HCA","AON","REGN","EQIX",
        "EMR","PSA","FCX","KLAC","ADP","ETN","ROP","GD","MCO",

        # Mid Caps
        "ROKU","SHOP","SQ","PLTR","COIN","AFRM","UPST","CRWD","NET","DDOG",
        "ZS","SNOW","RIVN","LCID","SOFI","DKNG","MARA","RIOT","FUBO","PENN",

        # Known small caps
        "SNDL","MULN","NKLA","BBIG","ATER","GME","AMC","BB","TLRY","CLOV"
    ]


# -----------------------------
# AUTO DISCOVER PENNY STOCKS
# -----------------------------
def get_dynamic_pennies():
    candidates = ["SNDL","MULN","NKLA","BBIG","ATER","CLOV","TLRY","BB","WKHS","GPRO"]
    penny_list = []

    try:
        tickers = yf.Tickers(" ".join(candidates))

        for symbol in tickers.tickers:
            df = tickers.tickers[symbol].history(period="5d")

            if df.empty:
                continue

            price = df["Close"].iloc[-1]
            volume = df["Volume"].iloc[-1]

            if price < 5 and volume > 1_000_000:
                penny_list.append(symbol)

    except:
        pass

    return penny_list


# -----------------------------
# RSI
# -----------------------------
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# -----------------------------
# FIX MULTI-INDEX COLUMNS
# -----------------------------
def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


# -----------------------------
# BUILD DATASET
# -----------------------------
def build_dataset():

    symbols = get_universe()
    symbols += get_dynamic_pennies()
    symbols = list(set(symbols))

    all_rows = []

    print(f"Scanning {len(symbols)} stocks...")

    for symbol in symbols:
        try:
            print(f"Downloading {symbol}...")

            df = yf.download(symbol, period="3y", interval="1d", progress=False)

            if df.empty:
                continue

            df = flatten_columns(df)

            # FEATURES
            df["ma20"] = df["Close"].rolling(20).mean()
            df["ma50"] = df["Close"].rolling(50).mean()
            df["rsi"] = compute_rsi(df["Close"])
            df["atr"] = (df["High"] - df["Low"]).rolling(14).mean()

            # FUTURE RETURN
            df["future_return"] = df["Close"].shift(-5) / df["Close"] - 1
            df = df.dropna(subset=["future_return"])

            # LONG ONLY TARGET
            df["target"] = (df["future_return"] > 0.03).astype(int)

            df = df[["ma20","ma50","rsi","atr","target"]]
            df = df.dropna()

            if len(df) == 0:
                continue

            all_rows.append(df)

            sleep(0.3)

        except Exception as e:
            print("Error:", symbol, e)
            continue

    if len(all_rows) == 0:
        print("No valid data downloaded.")
        return

    dataset = pd.concat(all_rows)
    dataset.to_csv("training_data.csv", index=False)

    print("\nDataset saved.")
    print("Total rows:", len(dataset))


if __name__ == "__main__":
    build_dataset()