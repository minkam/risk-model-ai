import os
import datetime
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from zoneinfo import ZoneInfo

from scan_engine import scan_market

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 RiskModel Momentum Engine Online\n\n"
        "/scan\n"
        "/eod\n"
        "/open"
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, scan_market)

    if not results:
        await update.message.reply_text("🔥 LIVE SETUPS\n\nNo strong momentum setups.")
        return

    message = "🔥 TOP MOMENTUM SETUPS\n\n"

    for r in results:
        message += (
            f"{r['symbol']} | Score: {r['score']}\n"
            f"Entry: {r['entry']} | Stop: {r['stop']} | Target: {r['target']}\n"
            f"Size: {r['size']}\n\n"
        )

    await update.message.reply_text(message)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))

    print("Bot running...")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()