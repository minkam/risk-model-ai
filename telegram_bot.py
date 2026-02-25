import os
import pytz
import yfinance as yf
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from scan_today import run_scan

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
eastern = pytz.timezone("US/Eastern")

alerted_symbols = set()


# -----------------------------
# MARKET DATA HELPERS
# -----------------------------

def get_index_change(symbol):
    df = yf.download(symbol, period="2d", interval="1d", progress=False)
    if df.empty or len(df) < 2:
        return None

    close_today = df["Close"].iloc[-1]
    close_yesterday = df["Close"].iloc[-2]

    return round((close_today / close_yesterday - 1) * 100, 2)


def end_of_day_report():

    spy = get_index_change("SPY")
    qqq = get_index_change("QQQ")
    dia = get_index_change("DIA")

    signals = run_scan()
    top = signals[:5]

    report = "📊 End of Day Report\n\n"
    report += f"SPY: {spy}%\nQQQ: {qqq}%\nDIA: {dia}%\n\n"

    if top:
        report += "Top High-Probability Swings:\n"
        for symbol, prob in top:
            report += f"{symbol} ({round(prob,3)})\n"
    else:
        report += "No strong swing setups today."

    return report


def market_open_report():

    signals = run_scan()
    top = signals[:5]

    report = "🔔 Market Open Report\n\n"

    if top:
        report += "Top Pre-Market Swing Candidates:\n"
        for symbol, prob in top:
            report += f"{symbol} ({round(prob,3)})\n"
    else:
        report += "No strong setups at open."

    return report


# -----------------------------
# COMMANDS
# -----------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.bot_data["chat_id"] = update.effective_chat.id
    await update.message.reply_text(
        "🚀 Swing AI Online\nCommands:\n"
        "/scan\n"
        "/status\n"
        "/eod\n"
        "/open"
    )


async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    signals = run_scan()

    if not signals:
        await update.message.reply_text("No strong setups right now.")
        return

    message = "🚀 High-Probability 3–5 Day Long Setups\n\n"

    for symbol, prob in signals:
        message += f"{symbol} | {round(prob,3)}\n"

    await update.message.reply_text(message)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Engine running. Monitoring markets.")


async def eod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(end_of_day_report())


async def open_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(market_open_report())


# -----------------------------
# AUTO ALERTS
# -----------------------------

async def auto_alert_job(context: ContextTypes.DEFAULT_TYPE):

    chat_id = context.bot_data.get("chat_id")
    if not chat_id:
        return

    signals = run_scan()

    for symbol, prob in signals:
        if symbol not in alerted_symbols:
            alerted_symbols.add(symbol)

            await context.bot.send_message(
                chat_id,
                f"🚨 NEW SWING ALERT\n\n{symbol}\nProbability: {round(prob,3)}"
            )


async def scheduled_reports(context: ContextTypes.DEFAULT_TYPE):

    chat_id = context.bot_data.get("chat_id")
    if not chat_id:
        return

    now = datetime.now(eastern).time()

    # 9:20 AM
    if now.hour == 9 and now.minute == 20:
        await context.bot.send_message(chat_id, market_open_report())

    # 4:10 PM
    if now.hour == 16 and now.minute == 10:
        await context.bot.send_message(chat_id, end_of_day_report())


# -----------------------------
# MAIN
# -----------------------------

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("eod", eod))
    app.add_handler(CommandHandler("open", open_report))

    # Strong signal check every 30 min
    app.job_queue.run_repeating(auto_alert_job, interval=1800, first=20)

    # Check scheduled reports every minute
    app.job_queue.run_repeating(scheduled_reports, interval=60, first=30)

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()