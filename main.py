import os, threading, time, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
import threading, time, requests, os
from telegram.ext import ApplicationBuilder, CommandHandler

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is running on Render!"

def run_telegram_bot():
    app_bot = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    # add handlers...
    app_bot.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_telegram_bot, daemon=True).start()
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

TOKEN = os.getenv("BOT_TOKEN")

# Dictionary to store active ping threads per user
active_pings = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me a URL and I’ll keep pinging it every 60 seconds.\nUse /stop to stop pinging."
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_pings:
        active_pings[user_id]["stop"] = True
        await update.message.reply_text("🛑 Pinging stopped!")
    else:
        await update.message.reply_text("❌ You’re not running any ping right now.")

def ping_loop(user_id, url, context):
    while not active_pings[user_id]["stop"]:
        try:
            res = requests.get(url, timeout=10)
            msg = f"✅ [{time.ctime()}] {url} → {res.status_code}"
        except Exception as e:
            msg = f"⚠️ [{time.ctime()}] Failed to reach {url}\nError: {e}"
        context.bot.send_message(chat_id=user_id, text=msg)
        time.sleep(60)  # ping interval
    del active_pings[user_id]

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text.strip()

    if not url.startswith("http"):
        await update.message.reply_text("❌ Please send a valid URL (starting with http/https).")
        return

    if user_id in active_pings:
        await update.message.reply_text("⚠️ Already pinging! Use /stop first.")
        return

    active_pings[user_id] = {"stop": False}
    await update.message.reply_text(f"🔄 Started pinging {url} every 60 seconds.")

    # Start thread
    thread = threading.Thread(target=ping_loop, args=(user_id, url, context), daemon=True)
    thread.start()

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
