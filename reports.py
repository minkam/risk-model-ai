# reports.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

FMP_API_KEY = os.getenv("FMP_API_KEY")
BASE_URL = "https://financialmodelingprep.com/api/v3"

_s = requests.Session()
_s.headers.update({"User-Agent": "RiskModelBot/1.0"})


def _safe_get(url: str):
    try:
        r = _s.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def _fmp(endpoint: str):
    if not FMP_API_KEY:
        return []
    sep = "&" if "?" in endpoint else "?"
    return _safe_get(f"{BASE_URL}{endpoint}{sep}apikey={FMP_API_KEY}")


def generate_open_report():
    gainers = _fmp("/stock_market/gainers")[:10]
    actives = _fmp("/stock_market/actives")[:10]

    msg = "🔔 MARKET OPEN REPORT\n\n"

    if gainers:
        msg += "🔥 Top Gainers:\n"
        for s in gainers[:5]:
            msg += f"{s.get('symbol')} | {s.get('changesPercentage')} | ${s.get('price')}\n"
        msg += "\n"

    if actives:
        msg += "⚡ Most Active:\n"
        for s in actives[:5]:
            msg += f"{s.get('symbol')} | {s.get('changesPercentage')} | Vol: {s.get('volume')}\n"

    return msg.strip()


def generate_eod_report():
    gainers = _fmp("/stock_market/gainers")[:15]
    losers = _fmp("/stock_market/losers")[:15]
    actives = _fmp("/stock_market/actives")[:15]

    msg = "📊 END OF DAY REPORT\n\n"

    if gainers:
        msg += "🔥 Biggest Winners:\n"
        for s in gainers[:7]:
            msg += f"{s.get('symbol')} | {s.get('changesPercentage')} | ${s.get('price')}\n"
        msg += "\n"

    if losers:
        msg += "📉 Biggest Losers:\n"
        for s in losers[:7]:
            msg += f"{s.get('symbol')} | {s.get('changesPercentage')} | ${s.get('price')}\n"
        msg += "\n"

    if actives:
        msg += "⚡ Highest Volume:\n"
        for s in actives[:7]:
            msg += f"{s.get('symbol')} | Vol: {s.get('volume')} | ${s.get('price')}\n"

    return msg.strip()