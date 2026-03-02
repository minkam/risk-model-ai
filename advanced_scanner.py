import requests
import os
from dotenv import load_dotenv

load_dotenv()

FMP_API_KEY = os.getenv("FMP_API_KEY")

BASE_URL = "https://financialmodelingprep.com/api/v3"

# ==============================
# LIVE STOCK WINNERS & LOSERS
# ==============================

def get_stock_movers():
    try:
        url = f"{BASE_URL}/stock_market/gainers?apikey={FMP_API_KEY}"
        gainers = requests.get(url).json()

        url = f"{BASE_URL}/stock_market/losers?apikey={FMP_API_KEY}"
        losers = requests.get(url).json()

        return gainers[:5], losers[:5]
    except:
        return [], []

# ==============================
# LIVE CRYPTO MOVERS
# ==============================

def get_crypto_movers():
    try:
        url = f"{BASE_URL}/cryptocurrency/list?apikey={FMP_API_KEY}"
        data = requests.get(url).json()

        # Sort by % change 24h
        sorted_data = sorted(data, key=lambda x: float(x.get("changesPercentage", 0)), reverse=True)

        winners = sorted_data[:5]
        losers = sorted_data[-5:]

        return winners, losers
    except:
        return [], []

# ==============================
# SETUP SCANNER (Momentum Breakout)
# ==============================

def scan_market():
    stock_setups = []
    crypto_setups = []

    try:
        gainers_url = f"{BASE_URL}/stock_market/gainers?apikey={FMP_API_KEY}"
        stocks = requests.get(gainers_url).json()

        for s in stocks[:10]:
            price = float(s["price"])
            change = float(s["changesPercentage"].replace("%",""))

            if change > 3:
                stop = round(price * 0.97, 2)
                risk = 0.01
                size = round((100000 * risk) / (price - stop), 2)

                stock_setups.append({
                    "ticker": s["symbol"],
                    "price": price,
                    "change": round(change,2),
                    "position_size": size,
                    "stop": stop
                })

    except:
        pass

    try:
        crypto_url = f"{BASE_URL}/cryptocurrency/list?apikey={FMP_API_KEY}"
        cryptos = requests.get(crypto_url).json()

        for c in cryptos:
            change = float(c.get("changesPercentage", 0))
            price = float(c.get("price", 0))

            if change > 4:
                stop = round(price * 0.96, 2)
                size = round((100000 * 0.01) / (price - stop), 2)

                crypto_setups.append({
                    "ticker": c["symbol"],
                    "price": price,
                    "change": round(change,2),
                    "position_size": size,
                    "stop": stop
                })

        crypto_setups = crypto_setups[:5]

    except:
        pass

    return {"stocks": stock_setups, "crypto": crypto_setups}

# ==============================
# END OF DAY REPORT
# ==============================

def generate_eod_report():
    stock_winners, stock_losers = get_stock_movers()
    crypto_winners, crypto_losers = get_crypto_movers()

    report = "📊 END OF DAY REPORT\n\n"

    report += "🔥 Top 5 Stock Winners:\n"
    for s in stock_winners:
        report += f"{s['symbol']} | {s['price']}$ | {s['changesPercentage']}\n"

    report += "\n📉 Top 5 Stock Losers:\n"
    for s in stock_losers:
        report += f"{s['symbol']} | {s['price']}$ | {s['changesPercentage']}\n"

    report += "\n🪙 Top 5 Crypto Winners:\n"
    for c in crypto_winners:
        report += f"{c['symbol']} | {c['price']}$ | {c['changesPercentage']}%\n"

    report += "\n📉 Top 5 Crypto Losers:\n"
    for c in crypto_losers:
        report += f"{c['symbol']} | {c['price']}$ | {c['changesPercentage']}%\n"

    return report

# ==============================
# MARKET OPEN REPORT
# ==============================

def generate_open_report():
    stock_winners, _ = get_stock_movers()
    crypto_winners, _ = get_crypto_movers()

    report = "🔔 MARKET OPEN REPORT\n\n"

    report += "🚀 Early Stock Momentum:\n"
    for s in stock_winners:
        report += f"{s['symbol']} | {s['changesPercentage']}\n"

    report += "\n🪙 Early Crypto Momentum:\n"
    for c in crypto_winners:
        report += f"{c['symbol']} | {c['changesPercentage']}%\n"

    return report