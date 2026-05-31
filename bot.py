import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== ПЕРЕМЕННЫЕ ИЗ ОКРУЖЕНИЯ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "mxslurp.click")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 2525))
MAILSLURP_USER = os.environ.get("MAILSLURP_USER")
MAILSLURP_PASS = os.environ.get("MAILSLURP_PASS")

# Проверка переменных
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не задан")
    exit(1)
if not MAILSLURP_USER or not MAILSLURP_PASS:
    logger.error("MAILSLURP_USER или MAILSLURP_PASS не заданы")
    exit(1)

logger.info(f"SMTP сервер: {SMTP_SERVER}:{SMTP_PORT}")
logger.info("Бот запускается...")

# Хранилище состояний пользователей
user_data = {}

# ========== ФУНКЦИЯ ОТПРАВКИ ПИСЬМА ==========
def send_spoof_email(from_email, to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = Header(subject, "utf-8").encode()
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
        server.starttls()
        server.login(MAILSLURP_USER, MAILSLURP_PASS)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        
        logger.info(f"Письмо отправлено: {from_email} -> {to_email}")
        return True, "✅ Письмо успешно отправлено!"
    except Exception as e:
        logger.error(f"SMTP ошибка: {e}")
        return False, f"❌ Ошибка: {str(e)[:150]}"

# ========== КОМАНДЫ БОТА ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"step": "from"}
    await update.message.reply_text(
        "📧 *Spoof Mailer Bot*\n\n"
        "Отправляю письма с любого фейкового email.\n\n"
        "Введите *от кого* (любой email, например `security@telegram.org`):",
        parse_mode="Markdown"
    )
    logger.info(f"Пользователь {user_id} начал работу")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]
    await update.message.reply_text(
        "❌ Отменено.\n\n"
        "Напишите /start для нового письма."
    )
    logger.info(f"Пользователь {user_id} отменил")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in user_data:
        await update.message.reply_text("Напишите /start для начала.")
        return
    
    step = user_data[user_id]["step"]
    
    if step == "from":
        user_data[user_id]["from"] = text
        user_data[user_id]["step"] = "to"
        await update.message.reply_text(
            f"📤 Отправитель: `{text}`\n\n"
            "Введите *получателя* (реальный email):",
            parse_mode="Markdown"
        )
    
    elif step == "to":
        user_data[user_id]["to"] = text
        user_data[user_id]["step"] = "subject"
        await update.message.reply_text(
            f"📥 Получатель: `{text}`\n\n"
            "Введите *тему* письма:",
            parse_mode="Markdown"
        )
    
    elif step == "subject":
        user_data[user_id]["subject"] = text
        user_data[user_id]["step"] = "body"
        await update.message.reply_text(
            f"📌 Тема: `{text}`\n\n"
            "Введите *текст* письма:",
            parse_mode="Markdown"
        )
    
    elif step == "body":
        user_data[user_id]["body"] = text
        data = user_data[user_id]
        
        await update.message.reply_text("⏳ Отправляю письмо...")
        
        success, msg = send_spoof_email(
            data["from"], 
            data["to"], 
            data["subject"], 
            data["body"]
        )
        
        await update.message.reply_text(
            f"{msg}\n\n"
            f"📨 От: `{data['from']}`\n"
            f"📬 Кому: `{data['to']}`\n"
            f"📎 Тема: `{data['subject']}`\n\n"
            "Напишите /start для нового письма.",
            parse_mode="Markdown"
        )
        
        del user_data[user_id]
        logger.info(f"Пользователь {user_id} отправил письмо на {data['to']}")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Бот успешно запущен и готов к работе!")
    app.run_polling()
