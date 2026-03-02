import os
import asyncio
import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from zoneinfo import ZoneInfo

from scan_engine import scan_market

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("Missing BOT_TOKEN or CHAT_ID")

scan_running = False


# ===============================
# COMMANDS
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Risk Model AI Online\n\n"
        "/scan – Live AI setups\n"
        "/eod – End of day report\n"
        "/open – Market open momentum"
    )


# ===============================
# LIVE SCAN (AI PROBABILITY)
# ===============================

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, scan_market)

    if not results:
        await update.message.reply_text(
            "🔥 LIVE MARKET SCAN\n\n"
            "No high-probability setups right now."
        )
        return

    message = "🔥 LIVE AI MOMENTUM SETUPS\n\n"

    for r in results:
        rr = round((r['target'] - r['entry']) / (r['entry'] - r['stop']), 2)

        message += (
            f"📈 {r['symbol']} | Prob: {r['prob']}\n"
            f"Entry: {r['entry']}\n"
            f"Stop: {r['stop']}\n"
            f"Target: {r['target']}\n"
            f"Risk/Reward: 1 : {rr}\n\n"
        )

    message += "⚡ Powered by Risk Model AI"

    await update.message.reply_text(message)


# ===============================
# EOD REPORT
# ===============================

async def eod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, scan_market)

    if not results:
        await update.message.reply_text("📊 EOD REPORT\n\nNo strong momentum today.")
        return

    message = "📊 END OF DAY REPORT\n\nTop Ranked:\n\n"

    for r in results[:5]:
        message += f"{r['symbol']} | Prob: {r['prob']}\n"

    await update.message.reply_text(message)


# ===============================
# MARKET OPEN REPORT
# ===============================

async def open_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, scan_market)

    if not results:
        await update.message.reply_text("🔔 MARKET OPEN\n\nNo early momentum.")
        return

    message = "🔔 MARKET OPEN MOMENTUM\n\n"

    for r in results[:5]:
        message += f"{r['symbol']} | Prob: {r['prob']}\n"

    await update.message.reply_text(message)


# ===============================
# AUTO ALERTS (Every 15 Min)
# ===============================

async def auto_scan(context: ContextTypes.DEFAULT_TYPE):
    global scan_running

    if scan_running:
        return

    scan_running = True

    try:
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, scan_market)

        if not results:
            return

        msg = "🚨 AUTO AI MOMENTUM ALERT\n\n"

        for r in results[:5]:
            rr = round((r['target'] - r['entry']) / (r['entry'] - r['stop']), 2)

            msg += (
                f"{r['symbol']} | Prob: {r['prob']}\n"
                f"Entry: {r['entry']} | Stop: {r['stop']} | Target: {r['target']}\n"
                f"R:R 1:{rr}\n\n"
            )

        await context.bot.send_message(chat_id=CHAT_ID, text=msg)

    finally:
        scan_running = False


# ===============================
# AUTO EOD (4:05 PM ET)
# ===============================

async def auto_eod(context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, scan_market)

    if not results:
        return

    msg = "📊 AUTO EOD SUMMARY\n\n"

    for r in results[:5]:
        msg += f"{r['symbol']} | Prob: {r['prob']}\n"

    await context.bot.send_message(chat_id=CHAT_ID, text=msg)


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

    # Every 15 minutes
    app.job_queue.run_repeating(auto_scan, interval=900, first=60)

    # Daily at 4:05 PM ET
    app.job_queue.run_daily(
        auto_eod,
        time=datetime.time(hour=16, minute=5, tzinfo=eastern)
    )

    print("Bot running...")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()