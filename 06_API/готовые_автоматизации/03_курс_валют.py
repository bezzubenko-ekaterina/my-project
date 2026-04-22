"""
Курс валют ЦБ РФ → красивое сообщение в Telegram.
Курс АССИСТ+

Зависимости: pip install requests python-dotenv
Запуск: python 03_курс_валют.py
Cron: 0 9 * * 1-5 python 03_курс_валют.py
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def get_rates():
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    r = requests.get(url, timeout=10)
    data = r.json()

    currencies = {
        "USD": {"emoji": "🇺🇸", "name": "Доллар"},
        "EUR": {"emoji": "🇪🇺", "name": "Евро"},
        "CNY": {"emoji": "🇨🇳", "name": "Юань"},
        "GBP": {"emoji": "🇬🇧", "name": "Фунт"},
        "TRY": {"emoji": "🇹🇷", "name": "Лира"},
        "KZT": {"emoji": "🇰🇿", "name": "Тенге"},
    }

    text = f"💱 <b>Курсы валют ЦБ РФ</b>\n📅 {datetime.now().strftime('%d.%m.%Y')}\n\n"

    for code, info in currencies.items():
        if code in data["Valute"]:
            v = data["Valute"][code]
            rate = v["Value"]
            prev = v["Previous"]
            nominal = v["Nominal"]
            per_unit = rate / nominal

            diff = rate - prev
            arrow = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
            sign = "+" if diff > 0 else ""

            text += f"{info['emoji']} <b>{code}</b> ({info['name']})\n"
            text += f"   {per_unit:.2f} ₽  {arrow} {sign}{diff/nominal:.2f}\n\n"

    return text


def send(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})


if __name__ == "__main__":
    send(get_rates())
    print("✅ Курсы отправлены")
