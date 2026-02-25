import os
import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from advanced_scanner import scan_market, generate_eod_report, generate_open_report

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ===============================
# COMMANDS
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Risk Model AI Online\n\n"
        "/scan\n"
        "/stocks\n"
        "/crypto\n"
        "/eod\n"
        "/open"
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = scan_market()

    message = "🔥 TOP MARKET SETUPS\n\n"

    if data["stocks"]:
        for s in data["stocks"]:
            message += f"{s['ticker']} | {s['price']}$ | {s['change']}%\n"
            message += f"Size: {s['position_size']} shares | Stop: {s['stop']}$\n\n"
    else:
        message += "No strong stock setups.\n\n"

    if data["crypto"]:
        for s in data["crypto"]:
            message += f"{s['ticker']} | {s['price']}$ | {s['change']}%\n"
            message += f"Size: {s['position_size']} units | Stop: {s['stop']}$\n\n"
    else:
        message += "No strong crypto setups.\n"

    await update.message.reply_text(message)

async def eod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    report = generate_eod_report()
    await update.message.reply_text(report)

async def open_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    report = generate_open_report()
    await update.message.reply_text(report)

async def auto_scan(context: ContextTypes.DEFAULT_TYPE):

    data = scan_market()

    if data["stocks"] or data["crypto"]:
        message = "🚨 NEW SETUP ALERT\n\n"

        for s in data["stocks"]:
            message += f"{s['ticker']} | {s['change']}%\n"

        for s in data["crypto"]:
            message += f"{s['ticker']} | {s['change']}%\n"

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

    app.job_queue.run_repeating(auto_scan, interval=600, first=10)
    app.job_queue.run_daily(auto_eod, time=datetime.time(hour=16, minute=5))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()