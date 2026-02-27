import os
import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from advanced_scanner import scan_market, generate_eod_report, generate_open_report

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN or CHAT_ID not found in .env")

# ===============================
# COMMANDS
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Risk Model AI Online\n"
        "/scan - Scan setups\n"
        "/stocks - Stock setups\n"
        "/crypto - Crypto setups\n"
        "/eod - End of Day Report\n"
        "/open - Market Open Report"
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = scan_market()

    message = "🔥 TOP MARKET SETUPS\n\nStocks:\n"
    if data["stocks"]:
        for s in data["stocks"]:
            message += f"{s['ticker']} | {s['price']}$ | {s['change']}%\n"
            message += f"Size: {s['position_size']} | Stop: {s['stop']}$\n\n"
    else:
        message += "No strong stock setups.\n\n"

    message += "Crypto:\n"
    if data["crypto"]:
        for c in data["crypto"]:
            message += f"{c['ticker']} | {c['price']}$ | {c['change']}%\n"
            message += f"Size: {c['position_size']} | Stop: {c['stop']}$\n\n"
    else:
        message += "No strong crypto setups.\n"

    await update.message.reply_text(message)

async def eod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    report = generate_eod_report()
    await update.message.reply_text(report)

async def open_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    report = generate_open_report()
    await update.message.reply_text(report)

# ===============================
# AUTO ALERTS
# ===============================

async def auto_scan(context: ContextTypes.DEFAULT_TYPE):
    data = scan_market()
    if data["stocks"] or data["crypto"]:
        message = "🚨 AUTO SETUP ALERT\n\n"

        if data["stocks"]:
            message += "Stocks:\n"
            for s in data["stocks"]:
                message += f"{s['ticker']} | {s['change']}% | Size {s['position_size']}\n"

        if data["crypto"]:
            message += "\nCrypto:\n"
            for c in data["crypto"]:
                message += f"{c['ticker']} | {c['change']}% | Size {c['position_size']}\n"

        await context.bot.send_message(chat_id=CHAT_ID, text=message)

async def auto_eod(context: ContextTypes.DEFAULT_TYPE):
    report = generate_eod_report()
    await context.bot.send_message(chat_id=CHAT_ID, text=report)

# ===============================
# MAIN
# ===============================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("stocks", scan))
    app.add_handler(CommandHandler("crypto", scan))
    app.add_handler(CommandHandler("eod", eod))
    app.add_handler(CommandHandler("open", open_market))

    # Auto scan every 10 minutes
    app.job_queue.run_repeating(auto_scan, interval=600, first=10)

    # Auto EOD report at 16:05 if needed
    app.job_queue.run_daily(auto_eod, time=datetime.time(hour=16, minute=5))

    print("Bot running.")
    app.run_polling()

if __name__ == "__main__":
    main()