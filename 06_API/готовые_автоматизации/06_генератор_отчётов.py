"""
Генератор отчётов — данные из CSV/JSON → красивый текстовый отчёт → Telegram.
Курс АССИСТ+

Что делает:
- Читает данные из CSV или JSON
- Считает метрики: всего, по статусам, конверсия
- Формирует красивый отчёт
- Отправляет в Telegram

Запуск: crontab -e → 0 18 * * 5 python 06_генератор_отчётов.py (каждую пятницу)
"""

import os
import csv
import json
from datetime import datetime, timedelta
from collections import Counter
from dotenv import load_dotenv
import requests

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ========== НАСТРОЙ ПОД СЕБЯ ==========
DATA_FILE = "data/leads.csv"  # Путь к файлу с данными

# Или создай тестовые данные:
SAMPLE_DATA = [
    {"name": "Иван", "status": "Новая", "source": "Telegram", "date": "2026-03-05"},
    {"name": "Мария", "status": "В работе", "source": "Instagram", "date": "2026-03-06"},
    {"name": "Пётр", "status": "Закрыта", "source": "Telegram", "date": "2026-03-07"},
    {"name": "Анна", "status": "Новая", "source": "Сайт", "date": "2026-03-08"},
    {"name": "Дмитрий", "status": "В работе", "source": "Рекомендация", "date": "2026-03-08"},
    {"name": "Елена", "status": "Закрыта", "source": "Telegram", "date": "2026-03-09"},
    {"name": "Сергей", "status": "Отказ", "source": "Instagram", "date": "2026-03-09"},
    {"name": "Ольга", "status": "Новая", "source": "Telegram", "date": "2026-03-10"},
    {"name": "Алексей", "status": "Закрыта", "source": "Сайт", "date": "2026-03-10"},
    {"name": "Наталья", "status": "В работе", "source": "Рекомендация", "date": "2026-03-10"},
]
# =======================================


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            reader = csv.DictReader(f)
            return list(reader)
    return SAMPLE_DATA


def generate_report(data):
    total = len(data)

    # По статусам
    statuses = Counter(d["status"] for d in data)

    # По источникам
    sources = Counter(d["source"] for d in data)

    # За последнюю неделю
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    this_week = [d for d in data if d.get("date", "") >= week_ago]

    # Конверсия
    closed = statuses.get("Закрыта", 0)
    conversion = (closed / total * 100) if total > 0 else 0

    # Формируем отчёт
    text = (
        f"📊 <b>Еженедельный отчёт</b>\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y')}\n\n"
        f"{'─' * 25}\n\n"
        f"📋 <b>Всего заявок:</b> {total}\n"
        f"📥 За эту неделю: {len(this_week)}\n\n"
    )

    # Статусы
    text += "📌 <b>По статусам:</b>\n"
    status_emojis = {"Новая": "🆕", "В работе": "⏳", "Закрыта": "✅", "Отказ": "❌"}
    for status, count in statuses.most_common():
        emoji = status_emojis.get(status, "•")
        bar = "▓" * int(count / total * 20) + "░" * (20 - int(count / total * 20))
        text += f"  {emoji} {status}: {count} ({count/total*100:.0f}%)\n"
        text += f"  {bar}\n"
    text += "\n"

    # Источники
    text += "📡 <b>По источникам:</b>\n"
    for source, count in sources.most_common():
        text += f"  • {source}: {count}\n"
    text += "\n"

    # Конверсия
    text += (
        f"{'─' * 25}\n"
        f"📈 <b>Конверсия:</b> {conversion:.1f}%\n"
        f"✅ Закрыто: {closed} из {total}\n"
    )

    return text


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})


if __name__ == "__main__":
    data = load_data()
    report = generate_report(data)
    print(report.replace("<b>", "").replace("</b>", ""))
    send_telegram(report)
    print("\n✅ Отчёт отправлен")
