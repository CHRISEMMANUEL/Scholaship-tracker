from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Replace with your token
TOKEN = "7769817844:AAFxHjub6Lasc8aGLmlTxDQlpgs1pWMBTyM"

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello 👋! I’m your Scholarship Tracker Bot. I’ll keep you updated on new scholarships.")

def main():
    # Create bot application
    app = Application.builder().token(TOKEN).build()

    # Add /start command
    app.add_handler(CommandHandler("start", start))

    print("Bot is running... Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
