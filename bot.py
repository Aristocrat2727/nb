import requests
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== ТОКЕН ИЗ ПЕРЕМЕННЫХ RAILWAY =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("BOT_TOKEN не задан в переменных Railway")
    exit(1)
# =======================================

# ===== ВСЁ ОСТАЛЬНОЕ ВШИТО =====
MAILGUN_DOMAIN = "sandbox65fd5df6fc5e43d5aa22050aa38e7b85.mailgun.org"
MAILGUN_API_KEY = "key-11ec613266855ec1166ee05d241a80d1"
# ===============================

user_data = {}

def send_mailgun(to_email, subject, body, from_email):
    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data={
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "text": body
            },
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"Письмо отправлено: {from_email} -> {to_email}")
            return True, "✅ Письмо отправлено через Mailgun!"
        else:
            logger.error(f"Mailgun ошибка: {response.status_code}")
            return False, f"❌ Ошибка Mailgun: {response.status_code}"
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return False, f"❌ Ошибка: {str(e)[:150]}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"step": "from"}
    await update.message.reply_text(
        "📧 *Mailgun Mailer Bot*\n\n"
        "Введите *от кого* (любой email, например security@telegram.org):\n"
        f"Или отправь 'default' чтобы использовать mailgun@{MAILGUN_DOMAIN}",
        parse_mode="Markdown"
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]
    await update.message.reply_text("❌ Отменено. /start")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_data:
        await update.message.reply_text("Напишите /start")
        return

    step = user_data[user_id]["step"]

    if step == "from":
        if text.lower() == "default":
            user_data[user_id]["from"] = f"mailgun@{MAILGUN_DOMAIN}"
        else:
            user_data[user_id]["from"] = text
        user_data[user_id]["step"] = "to"
        await update.message.reply_text("Введите *кому* (реальный email):", parse_mode="Markdown")

    elif step == "to":
        user_data[user_id]["to"] = text
        user_data[user_id]["step"] = "subject"
        await update.message.reply_text("Введите *тему* письма:", parse_mode="Markdown")

    elif step == "subject":
        user_data[user_id]["subject"] = text
        user_data[user_id]["step"] = "body"
        await update.message.reply_text("Введите *текст* письма:", parse_mode="Markdown")

    elif step == "body":
        user_data[user_id]["body"] = text
        data = user_data[user_id]

        await update.message.reply_text("⏳ Отправляю через Mailgun API...")
        success, msg = send_mailgun(data["to"], data["subject"], data["body"], data["from"])

        await update.message.reply_text(
            f"{msg}\n\n"
            f"📤 От: {data['from']}\n"
            f"📥 Кому: {data['to']}\n"
            f"📌 Тема: {data['subject']}\n\n"
            f"/start для нового"
        )
        del user_data[user_id]

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Mailgun бот запущен")
    app.run_polling()
