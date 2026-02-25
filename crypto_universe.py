import yfinance as yf

# Top crypto by market cap + high volatility movers
CRYPTO_LIST = [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "XRP-USD",
    "BNB-USD",
    "DOGE-USD",
    "ADA-USD",
    "AVAX-USD",
    "LINK-USD",
    "MATIC-USD",
    "DOT-USD",
    "ATOM-USD",
    "ARB-USD",
    "OP-USD",
    "APT-USD",
]

def get_active_crypto():
    active = []
    for symbol in CRYPTO_LIST:
        try:
            data = yf.download(symbol, period="5d", progress=False)
            if not data.empty:
                active.append(symbol)
        except:
            continue
    return active