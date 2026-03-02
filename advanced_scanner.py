import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

FMP_API_KEY = os.getenv("FMP_API_KEY")
BASE_URL = "https://financialmodelingprep.com/api/v3"

session = requests.Session()
session.headers.update({"User-Agent": "RiskModelBot/1.0"})

last_scan_time = 0
cached_data = None


# ===================================
# SAFE REQUEST
# ===================================

def safe_get(url):
    try:
        response = session.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


# ===================================
# STOCK MOMENTUM SCANNER (IMPROVED)
# ===================================

def scan_market():
    global last_scan_time, cached_data

    # Prevent spamming API within 60 sec
    if time.time() - last_scan_time < 60 and cached_data:
        return cached_data

    stock_setups = []
    crypto_setups = []

    # ===== STOCK SCAN =====
    stocks = safe_get(f"{BASE_URL}/stock_market/gainers?apikey={FMP_API_KEY}")

    for s in stocks[:15]:
        try:
            price = float(s["price"])
            change = float(s["changesPercentage"].replace("%", ""))
            volume = float(s.get("volume", 0))

            # Penny filter
            if price < 20 and change > 4 and volume > 500000:

                stop = round(price * 0.95, 2)
                risk = 0.01
                size = round((100000 * risk) / (price - stop), 2)

                stock_setups.append({
                    "ticker": s["symbol"],
                    "price": price,
                    "change": round(change, 2),
                    "position_size": size,
                    "stop": stop
                })

        except:
            continue

    # ===== CRYPTO SCAN (LIMITED SET) =====
    cryptos = safe_get(f"{BASE_URL}/cryptocurrency/list?apikey={FMP_API_KEY}")

    for c in cryptos[:50]:  # limit scanning size
        try:
            change = float(c.get("changesPercentage", 0))
            price = float(c.get("price", 0))

            if change > 5:

                stop = round(price * 0.94, 2)
                size = round((100000 * 0.01) / (price - stop), 2)

                crypto_setups.append({
                    "ticker": c["symbol"],
                    "price": price,
                    "change": round(change, 2),
                    "position_size": size,
                    "stop": stop
                })

        except:
            continue

    crypto_setups = sorted(crypto_setups, key=lambda x: x["change"], reverse=True)[:5]

    result = {"stocks": stock_setups, "crypto": crypto_setups}

    cached_data = result
    last_scan_time = time.time()

    return result


# ===================================
# EOD REPORT
# ===================================

def generate_eod_report():
    gainers = safe_get(f"{BASE_URL}/stock_market/gainers?apikey={FMP_API_KEY}")[:5]
    losers = safe_get(f"{BASE_URL}/stock_market/losers?apikey={FMP_API_KEY}")[:5]

    cryptos = safe_get(f"{BASE_URL}/cryptocurrency/list?apikey={FMP_API_KEY}")
    crypto_sorted = sorted(cryptos, key=lambda x: float(x.get("changesPercentage", 0)), reverse=True)

    crypto_winners = crypto_sorted[:5]
    crypto_losers = crypto_sorted[-5:]

    report = "📊 END OF DAY REPORT\n\n"

    report += "🔥 Top Stock Winners:\n"
    for s in gainers:
        report += f"{s['symbol']} | {s['price']}$ | {s['changesPercentage']}\n"

    report += "\n📉 Top Stock Losers:\n"
    for s in losers:
        report += f"{s['symbol']} | {s['price']}$ | {s['changesPercentage']}\n"

    report += "\n🪙 Top Crypto Winners:\n"
    for c in crypto_winners:
        report += f"{c['symbol']} | {c['price']}$ | {c['changesPercentage']}%\n"

    report += "\n📉 Top Crypto Losers:\n"
    for c in crypto_losers:
        report += f"{c['symbol']} | {c['price']}$ | {c['changesPercentage']}%\n"

    return report


# ===================================
# OPEN REPORT
# ===================================

def generate_open_report():
    gainers = safe_get(f"{BASE_URL}/stock_market/gainers?apikey={FMP_API_KEY}")[:5]

    report = "🔔 MARKET OPEN REPORT\n\n"

    for s in gainers:
        report += f"{s['symbol']} | {s['changesPercentage']}\n"

    return report