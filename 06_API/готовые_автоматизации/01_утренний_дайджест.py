"""
Утренний дайджест — погода + курс валют + задачи → Telegram.
Курс АССИСТ+

Запуск: crontab -e → 0 8 * * 1-5 python 01_утренний_дайджест.py
Зависимости: pip install requests python-dotenv
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ========== НАСТРОЙ ПОД СЕБЯ ==========
CITY = "Moscow"
TASKS = [  # Или подключи Todoist/Notion API
    "Проверить почту",
    "Ответить на заявки",
    "Подготовить отчёт",
]
# =======================================


def get_weather():
    try:
        url = f"https://wttr.in/{CITY}?format=%t+%C&lang=ru"
        r = requests.get(url, timeout=5)
        return r.text.strip()
    except:
        return "не удалось получить"


def get_exchange_rates():
    try:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        r = requests.get(url, timeout=5)
        data = r.json()
        usd = data["Valute"]["USD"]["Value"]
        eur = data["Valute"]["EUR"]["Value"]
        cny = data["Valute"]["CNY"]["Value"]
        return f"$ {usd:.2f}  € {eur:.2f}  ¥ {cny:.2f}"
    except:
        return "не удалось получить"


def format_digest():
    date = datetime.now().strftime("%d.%m.%Y, %A")
    weather = get_weather()
    rates = get_exchange_rates()

    tasks_text = "\n".join(f"  □ {t}" for t in TASKS)

    return (
        f"☀️ <b>Доброе утро!</b>\n"
        f"📅 {date}\n\n"
        f"🌤 Погода: {weather}\n"
        f"💱 Курсы: {rates}\n\n"
        f"📋 <b>Задачи на сегодня:</b>\n{tasks_text}\n\n"
        f"Хорошего дня! 🚀"
    )


def send(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})


if __name__ == "__main__":
    send(format_digest())
    print("✅ Дайджест отправлен")
