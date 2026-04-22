"""
АССИСТ+ | Модуль 06 — Пример API-запроса

Простой пример: отправка сообщения в Telegram через API.
В этом модуле мы работаем через Cursor — но полезно понимать, как API устроен изнутри.

Установка:
    pip install requests python-dotenv

Использование:
    1. Создай .env с ключами:
       TELEGRAM_BOT_TOKEN=...
       TELEGRAM_CHAT_ID=...
    2. Запусти: python пример_api_запроса.py

Или попроси Cursor: «Напиши скрипт, который отправляет сообщение в Telegram через Bot API».
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# URL — куда отправляем запрос
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# Тело запроса — данные в формате JSON
payload = {
    "chat_id": CHAT_ID,
    "text": f"Привет! Тестовое уведомление от {datetime.now().strftime('%H:%M %d.%m.%Y')}"
}

# Отправляем POST-запрос
response = requests.post(url, json=payload)

# Получаем ответ
if response.ok:
    print("Отправлено!")
else:
    print(f"Ошибка: {response.text}")
