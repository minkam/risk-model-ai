import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from advanced_scanner import scan_market, generate_eod_report, generate_open_report

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in .env")

# =========================
# COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """🚀 Risk Model AI Online

Commands:
/scan - Full Market Scan
/stocks - Stock Scan
/crypto - Crypto Scan
/eod - End of Day Report
/open - Market Open Report
"""
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = scan_market()
    message = "🔥 TOP MARKET SETUPS\n\n"

    for item in data[:10]:
        message += f"{item['ticker']} | ${item['price']} | {item['trend']}\n"

    await update.message.reply_text(message)

async def stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = scan_market(asset_type="stocks")

    message = "📈 STOCK SETUPS\n\n"

    for item in data[:10]:
        message += f"{item['ticker']} | ${item['price']} | {item['trend']}\n"

    await update.message.reply_text(message)

async def crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = scan_market(asset_type="crypto")

    message = "🪙 CRYPTO SETUPS\n\n"

    for item in data[:10]:
        message += f"{item['ticker']} | ${item['price']} | {item['trend']}\n"

    await update.message.reply_text(message)

async def eod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    report = generate_eod_report()
    await update.message.reply_text(report)

async def open_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    report = generate_open_report()
    await update.message.reply_text(report)

# =========================
# MAIN
# =========================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("stocks", stocks))
    app.add_handler(CommandHandler("crypto", crypto))
    app.add_handler(CommandHandler("eod", eod))
    app.add_handler(CommandHandler("open", open_market))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()