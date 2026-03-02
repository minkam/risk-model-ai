import os
import datetime
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from zoneinfo import ZoneInfo

from advanced_scanner import scan_market, generate_eod_report, generate_open_report

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN or CHAT_ID not found in .env")

scan_running = False  # prevents overlap


# ===============================
# COMMANDS
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Risk Model AI Online\n"
        "/scan\n"
        "/eod\n"
        "/open"
    )


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, scan_market)

    await update.message.reply_text(format_message(data))


async def eod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, generate_eod_report)
    await update.message.reply_text(report)


async def open_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, generate_open_report)
    await update.message.reply_text(report)


# ===============================
# AUTO ALERTS
# ===============================

async def auto_scan(context: ContextTypes.DEFAULT_TYPE):
    global scan_running

    if scan_running:
        return

    scan_running = True

    try:
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, scan_market)

        if data["stocks"] or data["crypto"]:
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=format_message(data, auto=True)
            )
    finally:
        scan_running = False


async def auto_eod(context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, generate_eod_report)
    await context.bot.send_message(chat_id=CHAT_ID, text=report)


# ===============================
# FORMATTER
# ===============================

def format_message(data, auto=False):
    message = "🚨 AUTO BREAKOUT ALERT\n\n" if auto else "🔥 LIVE MARKET SETUPS\n\n"

    if data["stocks"]:
        message += "Stocks:\n"
        for s in data["stocks"]:
            message += f"{s['ticker']} | {s['price']}$ | {s['change']}%\n"
            message += f"Size: {s['position_size']} | Stop: {s['stop']}$\n\n"

    if data["crypto"]:
        message += "Crypto:\n"
        for c in data["crypto"]:
            message += f"{c['ticker']} | {c['price']}$ | {c['change']}%\n"
            message += f"Size: {c['position_size']} | Stop: {c['stop']}$\n\n"

    if not data["stocks"] and not data["crypto"]:
        message += "No strong setups right now."

    return message


# ===============================
# MAIN
# ===============================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("eod", eod))
    app.add_handler(CommandHandler("open", open_market))

    eastern = ZoneInfo("America/New_York")

    app.job_queue.run_repeating(auto_scan, interval=600, first=10)
    app.job_queue.run_daily(auto_eod, time=datetime.time(hour=16, minute=5, tzinfo=eastern))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()