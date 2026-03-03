import os
import asyncio
import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from scan_engine import scan_market
from reports import generate_open_report, generate_eod_report

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")
if not CHAT_ID:
    raise ValueError("CHAT_ID missing")

scan_running = False


# ==========================================
# Format Output
# ==========================================

def format_setups(result):
    setups = result.get("setups", [])
    meta = result.get("meta", {})

    if not setups:
        return (
            "🔥 LIVE MARKET SCAN\n\n"
            "No strong setups right now.\n\n"
            f"Scanned: {meta.get('stocks_scanned',0)} stocks | "
            f"{meta.get('crypto_scanned',0)} crypto"
        )

    stocks = []
    crypto = []

    for s in setups:
        line = (
            f"{'🚀' if s['type']=='BREAKOUT' else '📈'} "
            f"{s['symbol']} | Score: {s['score']} | Prob: {s['prob']}\n"
            f"Entry: {s['entry']} | Stop: {s['stop']} | Target: {s['target']}\n"
        )

        if s["bucket"] == "CRYPTO":
            crypto.append("🪙 " + line)
        else:
            stocks.append(line)

    msg = "🔥 LIVE MARKET SETUPS\n\n"

    if stocks:
        msg += "📊 STOCK SETUPS\n"
        msg += "\n".join(stocks[:10])
        msg += "\n\n"

    if crypto:
        msg += "🪙 CRYPTO SETUPS\n"
        msg += "\n".join(crypto[:5])

    msg += (
        f"\n\nScanned: {meta.get('stocks_scanned',0)} stocks | "
        f"{meta.get('crypto_scanned',0)} crypto"
    )

    return msg.strip()


# ==========================================
# Commands
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Risk Model AI Online\n\n"
        "/scan - intraday 30m scan\n"
        "/open - market open movers\n"
        "/eod - end of day movers\n"
        "/help"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Intraday Small-Cap System\n\n"
        "• 30m breakout detection\n"
        "• Early + continuation alerts\n"
        "• Penny runner optimized\n"
        "• Crypto labeled separately\n"
        "• Auto scan every 10 min\n"
    )


async def scan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, scan_market)
    await update.message.reply_text(format_setups(result))


async def open_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, generate_open_report)
    await update.message.reply_text(report)


async def eod_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, generate_eod_report)
    await update.message.reply_text(report)


# ==========================================
# Auto Scanner (Every 10 Minutes)
# ==========================================

async def auto_scan(context: ContextTypes.DEFAULT_TYPE):
    global scan_running

    if scan_running:
        return

    scan_running = True

    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, scan_market)

        strong = [s for s in result.get("setups", []) if s["score"] >= 80]

        if strong:
            payload = {
                "setups": strong[:8],
                "meta": result.get("meta", {})
            }
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text="🚨 STRONG INTRADAY ALERT\n\n" + format_setups(payload)
            )

    except Exception as e:
        print("Auto scan error:", e)

    finally:
        scan_running = False


# ==========================================
# Auto Reports
# ==========================================

async def auto_open(context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, generate_open_report)
    await context.bot.send_message(chat_id=CHAT_ID, text=report)


async def auto_eod(context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, generate_eod_report)
    await context.bot.send_message(chat_id=CHAT_ID, text=report)


# ==========================================
# Main
# ==========================================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("scan", scan_cmd))
    app.add_handler(CommandHandler("open", open_cmd))
    app.add_handler(CommandHandler("eod", eod_cmd))

    eastern = ZoneInfo("America/New_York")

    # 10-minute scanner
    app.job_queue.run_repeating(auto_scan, interval=600, first=20)

    # Open report 9:35 ET
    app.job_queue.run_daily(auto_open, time=datetime.time(9, 35, tzinfo=eastern))

    # EOD report 4:10 ET
    app.job_queue.run_daily(auto_eod, time=datetime.time(16, 10, tzinfo=eastern))

    print("Bot running...")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()