import numpy as np
import joblib
import yfinance as yf
from universe import build_universe

MODEL_PATH = "swing_model.pkl"
model = joblib.load(MODEL_PATH)

def _prepare_features(df):
    df["return"] = df["Close"].pct_change()
    df["sma20"] = df["Close"].rolling(20).mean()
    df["sma50"] = df["Close"].rolling(50).mean()
    df["volatility"] = df["return"].rolling(10).std()
    df = df.dropna()
    return df

def _download_stock(symbol: str):
    return yf.download(symbol, period="6mo", interval="1d", progress=False)

def _download_crypto(symbol: str):
    # yfinance crypto tickers look like "BTC-USD"
    # Binance tickers come like "BTCUSDT" -> convert to "BTC-USD" style for yfinance
    if symbol.endswith("USDT"):
        base = symbol.replace("USDT", "")
        yf_sym = f"{base}-USD"
    else:
        yf_sym = symbol
    t = yf.Ticker(yf_sym)
    df = t.history(period="6mo", interval="1d")
    return df, yf_sym

def scan_symbol(symbol: str, is_crypto: bool):
    try:
        if is_crypto:
            df, mapped = _download_crypto(symbol)
            symbol_out = mapped
        else:
            df = _download_stock(symbol)
            symbol_out = symbol

        if df is None or df.empty or len(df) < 80:
            return None

        df = _prepare_features(df)
        latest = df.iloc[-1]

        X = np.array([[
            float(latest["return"]),
            float(latest["Close"] / latest["sma20"]),
            float(latest["Close"] / latest["sma50"]),
            float(latest["volatility"])
        ]])

        prob = float(model.predict_proba(X)[0][1])

        # High probability only
        if prob < 0.85:
            return None

        entry = float(latest["Close"])
        stop = entry * 0.95
        target = entry * 1.10

        return {
            "symbol": symbol_out,
            "prob": round(prob, 3),
            "entry": round(entry, 2),
            "stop": round(stop, 2),
            "target": round(target, 2),
        }

    except:
        return None

def scan_market():
    stocks, crypto = build_universe()
    results = []

    for s in stocks:
        r = scan_symbol(s, is_crypto=False)
        if r:
            results.append(r)

    for c in crypto:
        r = scan_symbol(c, is_crypto=True)
        if r:
            results.append(r)

    results.sort(key=lambda x: x["prob"], reverse=True)
    return results[:12]