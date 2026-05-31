# bot.py
# SWILL // 26.09.2025 // Без переменных — всё через Telegram

import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("BOT_TOKEN не задан")
    exit(1)

user_data = {}

def send_spoof_email(smtp_server, smtp_port, smtp_user, smtp_pass, from_email, to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = Header(subject, "utf-8").encode()
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        return True, "✅ Письмо отправлено!"
    except Exception as e:
        logger.error(f"SMTP ошибка: {e}")
        return False, f"❌ Ошибка: {str(e)[:150]}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"step": "smtp_server"}
    await update.message.reply_text(
        "📧 *Spoof Mailer Bot*\n\n"
        "Введите *SMTP сервер* (например: smtp.gmail.com):\n\n"
        "Или используйте MailSlurp: mxslurp.click",
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
    
    if step == "smtp_server":
        user_data[user_id]["smtp_server"] = text
        user_data[user_id]["step"] = "smtp_port"
        await update.message.reply_text("Введите *порт* (обычно 587, 465 или 2525):", parse_mode="Markdown")
    
    elif step == "smtp_port":
        try:
            user_data[user_id]["smtp_port"] = int(text)
            user_data[user_id]["step"] = "smtp_user"
            await update.message.reply_text("Введите *логин* SMTP (username/email):", parse_mode="Markdown")
        except:
            await update.message.reply_text("❌ Порт должен быть числом. Попробуйте ещё раз:")
    
    elif step == "smtp_user":
        user_data[user_id]["smtp_user"] = text
        user_data[user_id]["step"] = "smtp_pass"
        await update.message.reply_text("Введите *пароль* SMTP:", parse_mode="Markdown")
    
    elif step == "smtp_pass":
        user_data[user_id]["smtp_pass"] = text
        user_data[user_id]["step"] = "from_email"
        await update.message.reply_text("Введите *от кого* (фейковый email, например security@telegram.org):", parse_mode="Markdown")
    
    elif step == "from_email":
        user_data[user_id]["from_email"] = text
        user_data[user_id]["step"] = "to_email"
        await update.message.reply_text("Введите *кому* (реальный email получателя):", parse_mode="Markdown")
    
    elif step == "to_email":
        user_data[user_id]["to_email"] = text
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
        
        success, msg = send_spoof_email(
            data["smtp_server"],
            data["smtp_port"],
            data["smtp_user"],
            data["smtp_pass"],
            data["from_email"],
            data["to_email"],
            data["subject"],
            data["body"]
        )
        
        await update.message.reply_text(
            f"{msg}\n\n"
            f"📤 От: {data['from_email']}\n"
            f"📥 Кому: {data['to_email']}\n"
            f"📌 Тема: {data['subject']}\n\n"
            f"/start для нового"
        )
        del user_data[user_id]

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Бот запущен")
    app.run_polling()
