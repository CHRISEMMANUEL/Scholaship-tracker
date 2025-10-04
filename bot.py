import streamlit as st
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import sqlite3

TOKEN = bot_token = st.secrets["bot"]["BOT_TOKEN"]
USER_CHAT_ID = None  # Will store your chat id after /start

# Start command
# --- DB Helper to store chat IDs ---
def save_chat_id(chat_id):
    conn = sqlite3.connect("scholarships.db")
    cursor = conn.cursor()

    # Create table for subscribers if it doesn’t exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT UNIQUE
        )
    """)
    # Insert or ignore duplicate
    cursor.execute("INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()


def get_all_chat_ids():
    conn = sqlite3.connect("scholarships.db")
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM subscribers")
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids


# --- Bot Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    save_chat_id(chat_id)  # ✅ Save it to DB
    await update.message.reply_text(
        f"✅ You’re subscribed! I’ll notify you about new scholarships.\n\n🆔 Your Chat ID: `{chat_id}`",
        parse_mode="Markdown"
    )
    print(f"Chat ID saved: {chat_id}")


async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("scholarships.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, link, deadline FROM scholarships ORDER BY date_scraped DESC LIMIT 5")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        message = "📌 Latest Scholarships:\n\n"
        for title, link, deadline in rows:
            message += f"🎓 {title}\n⏳ Deadline: {deadline}\n🔗 {link}\n\n"
    else:
        message = "No scholarships found."

    await update.message.reply_text(message)


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("latest", latest))

    print("🤖 Bot is running... Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()