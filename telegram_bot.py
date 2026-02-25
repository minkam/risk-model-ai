import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

from advanced_scanner import scan_market

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in environment variables.")

# ===============================
# COMMANDS
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Risk Model AI Online\n\n"
        "Commands:\n"
        "/scan - Full Market Scan\n"
        "/stocks - Stock Scan\n"
        "/crypto - Crypto Scan\n"
        "/eod - End of Day Report\n"
        "/open - Market Open Report\n"
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = scan_market()

    if not data:
        await update.message.reply_text("No strong setups right now.")
        return

    message = "🚀 HIGH PROBABILITY SETUPS\n\n"
    for item in data[:10]:
        message += f"{item['symbol']} | Score: {round(item['score'],2)}\n"

    await update.message.reply_text(message)

async def stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = scan_market(asset_type="stocks")

    message = "📈 STOCK SETUPS\n\n"
    for item in data[:10]:
        message += f"{item['symbol']} | Score: {round(item['score'],2)}\n"

    await update.message.reply_text(message)

async def crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = scan_market(asset_type="crypto")

    message = "🪙 CRYPTO SETUPS\n\n"
    for item in data[:10]:
        message += f"{item['symbol']} | Score: {round(item['score'],2)}\n"

    await update.message.reply_text(message)

async def eod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 End of Day report coming soon.")

async def open_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔔 Market Open report coming soon.")

# ===============================
# MAIN
# ===============================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

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