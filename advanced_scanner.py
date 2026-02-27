import yfinance as yf
import pandas as pd

# ===============================
# MARKET UNIVERSES
# ===============================

STOCKS = [
    "AAPL","MSFT","NVDA","TSLA","AMD","AMZN","META","NFLX",
    "AVGO","JPM","BAC","GS","PLTR","SMCI","COIN","SOFI",
    "RIVN","LCID","NIO","GME","AMC","BB","FUBO","MAR"
]

CRYPTO = [
    "BTC-USD","ETH-USD","SOL-USD","DOGE-USD",
    "XRP-USD","ADA-USD","AVAX-USD","LINK-USD","LTC-USD"
]

PENNY_STOCKS = [
    "BB","FUBO","SNDL","NOK","PLUG","GEVO","CLNE","PNRG",
    "CLF","XELA","SPI","CGC","APHQ","BDR","BOTZ","LRN"
]

# ===============================
# SAFE DOWNLOAD
# ===============================

def download_data(tickers, period="5d"):
    try:
        data = yf.download(
            tickers=tickers,
            period=period,
            group_by="ticker",
            auto_adjust=True,
            threads=True,
            progress=False
        )
        return data
    except Exception:
        return None

# ===============================
# TOP MOVERS (WINNERS + LOSERS)
# ===============================

def get_movers(tickers):
    data = download_data(tickers)
    if data is None:
        return []

    movers = []
    for t in tickers:
        try:
            df = data[t].dropna()
            if len(df) < 2:
                continue

            close_today = float(df["Close"].iloc[-1])
            close_yesterday = float(df["Close"].iloc[-2])
            pct_change = ((close_today - close_yesterday) / close_yesterday) * 100

            movers.append((t, round(pct_change,2), round(close_today,2)))
        except Exception:
            continue

    return movers

def top_winners(tickers, n=5):
    movers = get_movers(tickers)
    movers.sort(key=lambda x: x[1], reverse=True)
    return movers[:n]

def top_losers(tickers, n=5):
    movers = get_movers(tickers)
    movers.sort(key=lambda x: x[1])  # ascending
    return movers[:n]

# ===============================
# SETUP SCANNER
# ===============================

def scan_market():
    all_symbols = STOCKS + PENNY_STOCKS + CRYPTO
    data = download_data(all_symbols)

    stock_setups = []
    crypto_setups = []

    if data is None:
        return {"stocks": [], "crypto": []}

    for sym in all_symbols:
        try:
            df = data[sym].dropna()
            if len(df) < 20:
                continue

            close = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2])
            volume = float(df["Volume"].iloc[-1])
            avg_vol = float(df["Volume"].rolling(20).mean().iloc[-1])
            change = ((close - prev) / prev) * 100

            # Simple breakout condition
            if change > 2 and volume > avg_vol:
                risk = 0.01  # 1% risk per trade
                stop = round(close * 0.97, 2)
                size = round((100000 * risk) / (close - stop), 2)

                setup = {
                    "ticker": sym,
                    "price": round(close,2),
                    "change": round(change,2),
                    "position_size": size,
                    "stop": stop
                }

                if sym.endswith("-USD"):
                    crypto_setups.append(setup)
                else:
                    stock_setups.append(setup)
        except Exception:
            continue

    return {"stocks": stock_setups, "crypto": crypto_setups}

# ===============================
# END OF DAY REPORT
# ===============================

def generate_eod_report():
    stock_winners = top_winners(STOCKS + PENNY_STOCKS)
    stock_losers = top_losers(STOCKS + PENNY_STOCKS)
    crypto_winners = top_winners(CRYPTO)
    crypto_losers = top_losers(CRYPTO)

    report = "📊 END OF DAY REPORT\n\n"

    report += "🔥 Top 5 Stock Winners:\n"
    for t,c,p in stock_winners:
        report += f"{t} | {p}$ | {c}%\n"

    report += "\n📉 Top 5 Stock Losers:\n"
    for t,c,p in stock_losers:
        report += f"{t} | {p}$ | {c}%\n"

    report += "\n🪙 Top 5 Crypto Winners:\n"
    for t,c,p in crypto_winners:
        report += f"{t} | {p}$ | {c}%\n"

    report += "\n📉 Top 5 Crypto Losers:\n"
    for t,c,p in crypto_losers:
        report += f"{t} | {p}$ | {c}%\n"

    return report

# ===============================
# MARKET OPEN REPORT
# ===============================

def generate_open_report():
    stock_winners = top_winners(STOCKS + PENNY_STOCKS)
    crypto_winners = top_winners(CRYPTO)

    report = "🔔 MARKET OPEN REPORT\n\n"
    report += "🚀 Early Stock Momentum:\n"
    for t,c,p in stock_winners:
        report += f"{t} | {c}% | {p}$\n"
    report += "\n🪙 Early Crypto Momentum:\n"
    for t,c,p in crypto_winners:
        report += f"{t} | {c}% | {p}$\n"
    return report