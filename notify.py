

import sqlite3
import requests
import streamlit as st

TELEGRAM_TOKEN = bot_token = st.secrets["bot"]["BOT_TOKEN"]


def get_all_chat_ids():
    """Fetch all subscriber chat IDs from DB."""
    conn = sqlite3.connect("scholarships.db")
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM subscribers")
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids


def send_telegram_message(text):
    """Send a message to ALL subscribed Telegram users."""
    chat_ids = get_all_chat_ids()
    if not chat_ids:
        print(" No subscribers found.")
        return

    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        try:
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                print(f" Message sent to {chat_id}")
            else:
                print(f" Failed for {chat_id}: {response.text}")
        except Exception as e:
            print(f" Error sending to {chat_id}: {e}")


def notify_new_scholarships():
    """Fetch latest scholarships from DB and notify via Telegram."""
    conn = sqlite3.connect("scholarships.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT title, link, deadline FROM scholarships ORDER BY date_scraped DESC LIMIT 3"
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        send_telegram_message("No new scholarships found today.")
        return

    message = "🎓 <b>Latest Scholarships</b>\n\n"
    for title, link, deadline in rows:
        message += f"📌 <b>{title}</b>\n⏳ Deadline: {deadline}\n🔗 {link}\n\n"

    send_telegram_message(message)


if __name__ == "__main__":
    notify_new_scholarships()
