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

# Публичный SMTP (рабочий на данный момент)
SMTP_SERVER = "smtp.titan.email"
SMTP_PORT = 587
SMTP_USER = "test@mail.bombuch.com"
SMTP_PASS = "rDNJncaYSM"

user_data = {}

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, [to_email], msg.as_string())
        server.quit()
        return True, "✅ Письмо отправлено!"
    except Exception as e:
        return False, f"❌ Ошибка: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"step": "to"}
    await update.message.reply_text(
        "📧 *Mailer Bot*\n\n"
        "Введите *email получателя*:",
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

    if step == "to":
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

        await update.message.reply_text("⏳ Отправляю...")
        success, msg = send_email(data["to"], data["subject"], data["body"])

        await update.message.reply_text(f"{msg}\n\n/start для нового")
        del user_data[user_id]

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
