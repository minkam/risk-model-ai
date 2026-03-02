import os
import datetime
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from zoneinfo import ZoneInfo

from scan_today import scan_market
from advanced_scanner import generate_eod_report, generate_open_report

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN or CHAT_ID not found in environment")

scan_running = False


# ===============================
# COMMANDS
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Risk Model AI Online\n\n"
        "/scan\n"
        "/eod\n"
        "/open"
    )


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, scan_market)

    if not results:
        await update.message.reply_text("🔥 LIVE MARKET SETUPS\n\nNo strong setups right now.")
        return

    message = "🔥 LIVE MARKET SETUPS\n\n"

    for r in results:
        message += (
            f"{r['symbol']} | Prob: {r['prob']}\n"
            f"Entry: {r['entry']} | Stop: {r['stop']} | Target: {r['target']}\n\n"
        )

    await update.message.reply_text(message)


async def eod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, generate_eod_report)
    await update.message.reply_text(report)


async def open_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, generate_open_report)
    await update.message.reply_text(report)


# ===============================
# AUTO JOBS
# ===============================

async def auto_scan(context: ContextTypes.DEFAULT_TYPE):
    global scan_running

    if scan_running:
        return

    scan_running = True

    try:
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, scan_market)

        if results:
            msg = "🚨 AUTO SIGNAL ALERT\n\n"

            for r in results:
                msg += (
                    f"{r['symbol']} | Prob: {r['prob']}\n"
                    f"Entry: {r['entry']} | Stop: {r['stop']} | Target: {r['target']}\n\n"
                )

            await context.bot.send_message(chat_id=CHAT_ID, text=msg)

    finally:
        scan_running = False


async def auto_eod(context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, generate_eod_report)
    await context.bot.send_message(chat_id=CHAT_ID, text=report)


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

    app.job_queue.run_repeating(auto_scan, interval=600, first=15)
    app.job_queue.run_daily(
        auto_eod,
        time=datetime.time(hour=16, minute=5, tzinfo=eastern)
    )

    print("Bot running...")

    # IMPORTANT: This prevents restart conflicts
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()