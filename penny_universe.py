import yfinance as yf
import pandas as pd

def find_penny_stocks():
    # Basic screener using Yahoo query
    # We pull popular tickers and filter manually

    tickers = yf.Tickers(" ".join([
        "SNDL","RIOT","MARA","PLUG","NKLA","FCEL","BB","GPRO","FUBO",
        "SOFI","OPEN","CLOV","NIO","LCID","HOOD","T","BBBYQ","WISH"
    ]))

    valid = []

    for symbol in tickers.tickers:
        try:
            df = tickers.tickers[symbol].history(period="3mo")

            if df.empty:
                continue

            price = df["Close"].iloc[-1]
            avg_vol = df["Volume"].mean()

            if 1 < price < 10 and avg_vol > 1_000_000:
                valid.append(symbol)

        except:
            continue

    return valid