"""
Связка: Telegram-бот + Google Sheets
Курс АССИСТ+, Модуль 06.

Бот принимает заявку → данные в таблицу → алерт менеджеру в Telegram.

Установка:
    pip install python-telegram-bot python-dotenv gspread requests

Настройка:
    1. Создай .env с ключами:
       TELEGRAM_BOT_TOKEN=...
       TELEGRAM_CHAT_ID=...  (твой Telegram ID через @userinfobot)
    2. Настрой Google Sheets API, скачай credentials.json
    3. Раскомментируй блок Google Sheets ниже
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import gspread
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)

load_dotenv()

# --- Конфиг ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MANAGER_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Google Sheets (раскомментируй после настройки)
# gc = gspread.service_account(filename="credentials.json")
# sheet = gc.open("Заявки").sheet1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_to_sheets(name: str, contact: str, text: str):
    """Сохраняет заявку в Google Sheets."""
    # Раскомментируй после настройки:
    # sheet.append_row([
    #     name,
    #     contact,
    #     text,
    #     datetime.now().strftime("%Y-%m-%d %H:%M"),
    #     "Новая"
    # ])
    logger.info(f"Saved to sheets: {name}, {contact}, {text}")


def notify_manager(name: str, contact: str, text: str):
    """Отправляет уведомление менеджеру в Telegram."""
    message = (
        f"<b>Новая заявка!</b>\n\n"
        f"<b>Имя:</b> {name}\n"
        f"<b>Контакт:</b> {contact}\n"
        f"<b>Текст:</b> {text}\n"
        f"<b>Время:</b> {datetime.now().strftime('%H:%M %d.%m.%Y')}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": MANAGER_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    })


# --- Обработчики ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для приёма заявок.\n\n"
        "Напишите ваше имя, контакт и опишите задачу."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user

    await update.message.reply_text("Обрабатываю вашу заявку...")

    try:
        name = user.full_name or "Не указано"
        contact = f"@{user.username}" if user.username else f"ID: {user.id}"

        save_to_sheets(name, contact, text)
        notify_manager(name, contact, text)

        await update.message.reply_text(
            "Заявка принята! Менеджер свяжется с вами в ближайшее время."
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        fallback_contact = os.getenv("FALLBACK_CONTACT", "@your_manager_username")
        await update.message.reply_text(
            f"Произошла ошибка. Пожалуйста, напишите напрямую: {fallback_contact}"
        )


# --- Запуск ---
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот-связка запущен (Telegram + Google Sheets)")
    app.run_polling()


if __name__ == "__main__":
    main()
