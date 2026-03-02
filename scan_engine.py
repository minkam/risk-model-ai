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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 RiskModel Engine Online\n\n"
        "/scan\n"
        "/eod\n"
        "/open"
    )


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, scan_market)

    message = "🔥 LIVE MARKET SETUPS\n\n"

    if results["penny"]:
        message += "💥 Penny Sniper\n"
        for r in results["penny"]:
            message += f"{r['symbol']} | Score: {r['score']} | Entry: {r['entry']}\n"
        message += "\n"

    if results["swings"]:
        message += "📈 Momentum Swings\n"
        for r in results["swings"]:
            message += f"{r['symbol']} | Score: {r['score']} | Entry: {r['entry']}\n"
        message += "\n"

    if results["crypto"]:
        message += "🪙 Crypto Movers\n"
        for r in results["crypto"]:
            message += f"{r['symbol']} | {r['change']}%\n"

    if message.strip() == "🔥 LIVE MARKET SETUPS":
        message += "\nNo strong setups."

    await update.message.reply_text(message)


async def auto_alert(context: ContextTypes.DEFAULT_TYPE):
    results = scan_market()

    if results["penny"] or results["swings"]:
        msg = "🚨 AUTO MOMENTUM ALERT\n\n"

        for r in results["penny"] + results["swings"]:
            msg += f"{r['symbol']} | Score: {r['score']} | Entry: {r['entry']}\n"

        await context.bot.send_message(chat_id=CHAT_ID, text=msg)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))

    eastern = ZoneInfo("America/New_York")

    app.job_queue.run_repeating(auto_alert, interval=600, first=60)

    print("Bot running...")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
