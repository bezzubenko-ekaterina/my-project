"""
Автопостинг в Telegram-канал — по расписанию или из файла.
Курс АССИСТ+

Что делает:
- Читает посты из файла posts.json
- Публикует по одному в Telegram-канал
- Поддерживает форматирование, кнопки, отложенную публикацию

Зависимости: pip install requests python-dotenv
"""

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ========== НАСТРОЙ ПОД СЕБЯ ==========
CHANNEL_ID = "@your_channel"  # Username канала или числовой ID
POSTS_FILE = "posts.json"
# =======================================


def create_sample_posts():
    """Создаёт файл с примерами постов."""
    posts = [
        {
            "text": (
                "🚀 <b>5 задач, которые нужно делегировать прямо сейчас</b>\n\n"
                "1. Ответы на однотипные письма\n"
                "2. Ведение календаря и напоминания\n"
                "3. Подготовка отчётов из таблиц\n"
                "4. Публикация контента в соцсетях\n"
                "5. Первичная фильтрация заявок\n\n"
                "Если делаете хотя бы 2 пункта сами — вам нужен ассистент.\n\n"
                "#делегирование #ассистент"
            ),
            "button_text": "Подобрать ассистента",
            "button_url": "https://t.me/assist_plus",
            "published": False,
        },
        {
            "text": (
                "💡 <b>Как выбрать бизнес-ассистента: 3 ключевых вопроса</b>\n\n"
                "1️⃣ <b>Какие задачи вы хотите отдать?</b>\n"
                "Составьте список за неделю. Всё, что повторяется — кандидат на делегирование.\n\n"
                "2️⃣ <b>Удалённо или в офисе?</b>\n"
                "90% задач можно делать удалённо. Экономия на рабочем месте.\n\n"
                "3️⃣ <b>Полная занятость или частичная?</b>\n"
                "Начните с 4 часов/день. Потом увеличите, если нужно.\n\n"
                "#советы #наём"
            ),
            "published": False,
        },
        {
            "text": (
                "📊 <b>Кейс: как ассистент сэкономил 60 часов в месяц</b>\n\n"
                "Клиент: IT-предприниматель, 3 проекта.\n"
                "Проблема: тонет в рутине, не успевает стратегию.\n\n"
                "Что делегировали:\n"
                "• Почта и мессенджеры — 2 ч/день\n"
                "• Документооборот — 1 ч/день\n"
                "• Контроль подрядчиков — 30 мин/день\n\n"
                "Результат: 3 часа в день × 20 дней = <b>60 часов</b> на стратегию.\n\n"
                "#кейс #результаты"
            ),
            "published": False,
        },
    ]

    with open(POSTS_FILE, "w") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f"📝 Создан {POSTS_FILE} с {len(posts)} постами")


def load_posts():
    if not os.path.exists(POSTS_FILE):
        create_sample_posts()
    with open(POSTS_FILE) as f:
        return json.load(f)


def save_posts(posts):
    with open(POSTS_FILE, "w") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def publish_next():
    posts = load_posts()

    # Находим первый неопубликованный
    for i, post in enumerate(posts):
        if not post.get("published"):
            text = post["text"]

            # Собираем кнопки (если есть)
            reply_markup = None
            if "button_text" in post and "button_url" in post:
                reply_markup = json.dumps({
                    "inline_keyboard": [[{
                        "text": post["button_text"],
                        "url": post["button_url"]
                    }]]
                })

            # Публикуем
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {
                "chat_id": CHANNEL_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup

            r = requests.post(url, json=payload)

            if r.ok:
                posts[i]["published"] = True
                posts[i]["published_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_posts(posts)
                print(f"✅ Пост #{i+1} опубликован")
                return True
            else:
                print(f"❌ Ошибка: {r.text}")
                return False

    print("📭 Все посты опубликованы")
    return False


if __name__ == "__main__":
    publish_next()
