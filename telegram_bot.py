import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from scan_engine import scan_market, generate_eod_report, generate_open_report

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Risk Model AI Online\n\n"
        "/scan\n"
        "/open\n"
        "/eod"
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, scan_market)

    if not results:
        await update.message.reply_text("No strong momentum setups found.")
        return

    message = "🔥 LIVE MOMENTUM SETUPS\n\n"

    for r in results:
        message += f"{r['symbol']} | Prob: {r['prob']}% | ${r['price']}\n"

    await update.message.reply_text(message)

async def eod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, generate_eod_report)
    await update.message.reply_text(report)

async def open_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, generate_open_report)
    await update.message.reply_text(report)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("eod", eod))
    app.add_handler(CommandHandler("open", open_market))

    print("Bot running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()