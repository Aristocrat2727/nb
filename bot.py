import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("BOT_TOKEN не задан")
    exit(1)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "namegazan@gmail.com"
SMTP_PASS = "dkhufoiqbvxbxftf"

user_data = {}

def send_email(to_email, subject, body, from_email):
    try:
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        return True, "✅ Письмо отправлено!"
    except Exception as e:
        return False, f"❌ Ошибка: {str(e)[:150]}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"step": "from"}
    await update.message.reply_text(
        "📧 *Gmail Mailer Bot*\n\n"
        "Введите *от кого* (любой email):\n"
        f"Или отправь 'default' чтобы использовать {SMTP_USER}",
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
            user_data[user_id]["from"] = SMTP_USER
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

        await update.message.reply_text("⏳ Отправляю через Gmail SMTP...")
        success, msg = send_email(data["to"], data["subject"], data["body"], data["from"])

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
    logger.info("Gmail SMTP бот запущен")
    app.run_polling()
