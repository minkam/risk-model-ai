import os
from datetime import time as dtime
import pytz
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from advanced_scanner import (
    scan_market,
    stock_setups,
    crypto_setups,
    generate_eod_report,
    generate_open_report,
)

load_dotenv()

# ENV VARS (use these exact names)
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")  # optional for later

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found. Put TELEGRAM_TOKEN=... in your .env or Railway Variables.")

TZ = pytz.timezone("America/Indiana/Indianapolis")


def _get_chat_id(context: ContextTypes.DEFAULT_TYPE, update: Update | None = None):
    """
    Use this priority:
      1) stored in bot_data (set on /start)
      2) current update chat id
    """
    chat_id = context.bot_data.get("chat_id")
    if chat_id:
        return chat_id
    if update and update.effective_chat:
        return update.effective_chat.id
    return None


def _fmt_setups(title: str, setups: list, asset: str) -> str:
    lines = [title, ""]
    if not setups:
        lines.append(f"No strong {asset} setups.")
        return "\n".join(lines)

    for s in setups[:10]:
        if asset == "stock":
            lines.append(f"- {s['symbol']} | {s['direction']} | ${s['price']} | {s['pct']}% | Vol {s['volume']:,}")
        else:
            lines.append(f"- {s['symbol']} ({s['name']}) | {s['direction']} | ${s['price']} | {s['pct_24h']}% 24h | Vol ${s['vol_24h']:,}")

    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # store chat_id so scheduled jobs know where to send messages
    context.bot_data["chat_id"] = update.effective_chat.id

    msg = (
        "🚀 Risk Model AI Online\n\n"
        "/scan\n"
        "/stocks\n"
        "/crypto\n"
        "/eod\n"
        "/open\n"
    )
    await update.message.reply_text(msg)


async def chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    await update.message.reply_text(f"✅ Your chat_id is: {cid}\n(I saved it for alerts.)")
    context.bot_data["chat_id"] = cid


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = scan_market()
    stocks = data.get("stocks", [])
    crypto = data.get("crypto", [])

    msg_lines = ["🔥 TOP MARKET SETUPS", ""]
    msg_lines.append("📈 STOCKS:")
    if not stocks:
        msg_lines.append("No strong stock setups.")
    else:
        for s in stocks[:5]:
            msg_lines.append(f"- {s['symbol']} | {s['direction']} | ${s['price']} | {s['pct']}% | Vol {s['volume']:,}")

    msg_lines.append("\n🪙 CRYPTO:")
    if not crypto:
        msg_lines.append("No strong crypto setups.")
    else:
        for s in crypto[:5]:
            msg_lines.append(f"- {s['symbol']} ({s['name']}) | {s['direction']} | ${s['price']} | {s['pct_24h']}% 24h | Vol ${s['vol_24h']:,}")

    await update.message.reply_text("\n".join(msg_lines))


async def stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    setups = stock_setups(limit=10)
    msg = _fmt_setups("📈 STOCK SETUPS", setups, asset="stock")
    await update.message.reply_text(msg)


async def crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    setups = crypto_setups(limit=10)
    msg = _fmt_setups("🪙 CRYPTO SETUPS", setups, asset="crypto")
    await update.message.reply_text(msg)


async def eod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    report = generate_eod_report()
    await update.message.reply_text(report)


async def open_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    report = generate_open_report()
    await update.message.reply_text(report)


# -----------------------
# AUTO JOBS
# -----------------------
async def auto_scan(context: ContextTypes.DEFAULT_TYPE):
    chat_id = _get_chat_id(context)
    if not chat_id:
        return

    data = scan_market()
    stocks = data.get("stocks", [])
    crypto = data.get("crypto", [])

    # Only alert if something exists
    if not stocks and not crypto:
        return

    lines = ["🚨 NEW SETUP ALERT", ""]
    if stocks:
        lines.append("📈 STOCKS:")
        for s in stocks[:3]:
            lines.append(f"- {s['symbol']} | ${s['price']} | {s['pct']}% | Vol {s['volume']:,}")
    if crypto:
        lines.append("\n🪙 CRYPTO:")
        for s in crypto[:3]:
            lines.append(f"- {s['symbol']} | ${s['price']} | {s['pct_24h']}% 24h | Vol ${s['vol_24h']:,}")

    await context.bot.send_message(chat_id, "\n".join(lines))


async def auto_open(context: ContextTypes.DEFAULT_TYPE):
    chat_id = _get_chat_id(context)
    if not chat_id:
        return
    await context.bot.send_message(chat_id, generate_open_report())


async def auto_eod(context: ContextTypes.DEFAULT_TYPE):
    chat_id = _get_chat_id(context)
    if not chat_id:
        return
    await context.bot.send_message(chat_id, generate_eod_report())


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("chatid", chatid))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("stocks", stocks))
    app.add_handler(CommandHandler("crypto", crypto))
    app.add_handler(CommandHandler("eod", eod))
    app.add_handler(CommandHandler("open", open_market))

    # AUTO SCAN every 10 minutes
    app.job_queue.run_repeating(auto_scan, interval=600, first=20)

    # Auto "market open" + EOD (Mon–Fri)
    # Market open report: 9:35 AM ET
    app.job_queue.run_daily(auto_open, time=dtime(hour=9, minute=35, tzinfo=TZ), days=(0, 1, 2, 3, 4))
    # EOD report: 4:10 PM ET
    app.job_queue.run_daily(auto_eod, time=dtime(hour=16, minute=10, tzinfo=TZ), days=(0, 1, 2, 3, 4))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()