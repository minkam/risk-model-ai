
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from scan_engine import scan_market
from advanced_scanner import generate_eod_report, generate_open_report

load_dotenv()

# ✅ USE TELEGRAM_TOKEN (NOT BOT_TOKEN)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found. Check your .env file or Railway variables.")


# =========================
# COMMAND HANDLERS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Risk Model AI Online\n\n"
        "Commands:\n"
        "/scan - Full Market Scan\n"
        "/stocks - Stock Scan\n"
        "/crypto - Crypto Scan\n"
        "/eod - End of Day Report\n"
        "/open - Market Open Report"
    )


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Scanning full market...")

    results = scan_market(mode="all")

    if not results:
        await update.message.reply_text("No strong setups found.")
        return

    message = "🔥 TOP MARKET SETUPS\n\n"

    for r in results[:10]:
        message += f"{r['symbol']} | Score: {r['score']:.2f}\n"

    await update.message.reply_text(message)


async def stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 Scanning stocks...")

    results = scan_market(mode="stocks")

    if not results:
        await update.message.reply_text("No strong stock setups.")
        return

    message = "📈 STOCK SETUPS\n\n"

    for r in results[:10]:
        message += f"{r['symbol']} | Score: {r['score']:.2f}\n"

    await update.message.reply_text(message)


async def crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🪙 Scanning crypto...")

    results = scan_market(mode="crypto")

    if not results:
        await update.message.reply_text("No strong crypto setups.")
        return

    message = "🪙 CRYPTO SETUPS\n\n"

    for r in results[:10]:
        message += f"{r['symbol']} | Score: {r['score']:.2f}\n"

    await update.message.reply_text(message)


async def eod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Generating End of Day report...")

    report = generate_eod_report()

    await update.message.reply_text(report)


async def open_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔔 Generating Market Open report...")

    report = generate_open_report()

    await update.message.reply_text(report)


# =========================
# MAIN
# =========================

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("stocks", stocks))
    app.add_handler(CommandHandler("crypto", crypto))
    app.add_handler(CommandHandler("eod", eod))
    app.add_handler(CommandHandler("open", open_report))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()