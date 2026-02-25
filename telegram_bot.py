import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from advanced_scanner import scan_market

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found. Check your .env file.")

# ----------------------------
# COMMAND HANDLERS
# ----------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "🚀 Risk Model AI Online\n\n"
        "Commands:\n"
        "/scan - Full Market Scan\n"
        "/stocks - Stock Scan\n"
        "/crypto - Crypto Scan\n"
        "/eod - End of Day Report\n"
        "/open - Market Open Report\n"
    )
    await update.message.reply_text(message)


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = scan_market()

    if not data:
        await update.message.reply_text("No strong setups right now.")
        return

    message = "🔥 TOP MARKET SETUPS\n\n"

    stocks = data.get("stocks", [])
    crypto = data.get("crypto", [])

    if stocks:
        message += "📈 STOCKS:\n"
        for s in stocks[:5]:
            message += f"{s['symbol']} | Score: {s['score']:.2f}\n"
        message += "\n"

    if crypto:
        message += "🪙 CRYPTO:\n"
        for c in crypto[:5]:
            message += f"{c['symbol']} | Score: {c['score']:.2f}\n"

    await update.message.reply_text(message)


async def stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = scan_market()

    stocks = data.get("stocks", [])

    if not stocks:
        await update.message.reply_text("No strong stock setups.")
        return

    message = "📈 STOCK SETUPS\n\n"
    for s in stocks[:10]:
        message += f"{s['symbol']} | Score: {s['score']:.2f}\n"

    await update.message.reply_text(message)


async def crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = scan_market()

    crypto = data.get("crypto", [])

    if not crypto:
        await update.message.reply_text("No strong crypto setups.")
        return

    message = "🪙 CRYPTO SETUPS\n\n"
    for c in crypto[:10]:
        message += f"{c['symbol']} | Score: {c['score']:.2f}\n"

    await update.message.reply_text(message)


async def eod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 End of Day report generating...")


async def open_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔔 Market Open report generating...")


# ----------------------------
# MAIN
# ----------------------------

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