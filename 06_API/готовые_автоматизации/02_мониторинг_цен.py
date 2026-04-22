"""
Мониторинг цен конкурентов — парсинг + сравнение + алерт в Telegram.
Курс АССИСТ+

Что делает:
- Парсит цены с указанных страниц
- Сравнивает с твоими ценами
- Если конкурент снизил цену — алерт в Telegram
- Сохраняет историю в JSON

Запуск: crontab -e → 0 10 * * 1-5 python 02_мониторинг_цен.py
Зависимости: pip install requests beautifulsoup4 python-dotenv
"""

import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Установи: pip install beautifulsoup4")
    exit(1)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HISTORY_FILE = "price_history.json"

# ========== НАСТРОЙ ПОД СЕБЯ ==========
MY_PRICES = {
    "Подбор ассистента": 50000,
    "Обучение": 30000,
    "Аудит": 25000,
}

COMPETITORS = [
    {
        "name": "Конкурент 1",
        "url": "https://example.com/prices",
        "selector": ".price-value",  # CSS-селектор цены
        "service": "Подбор ассистента",
    },
    {
        "name": "Конкурент 2",
        "url": "https://example2.com/services",
        "selector": ".service-price",
        "service": "Подбор ассистента",
    },
]
# =======================================


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {}


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def parse_price(url, selector):
    """Парсит цену со страницы."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        element = soup.select_one(selector)
        if element:
            # Извлекаем число из текста
            numbers = re.findall(r'[\d\s]+', element.get_text())
            if numbers:
                price = int(numbers[0].replace(" ", ""))
                return price
    except Exception as e:
        print(f"Ошибка парсинга {url}: {e}")
    return None


def check_prices():
    history = load_history()
    today = datetime.now().strftime("%Y-%m-%d")
    alerts = []

    for comp in COMPETITORS:
        price = parse_price(comp["url"], comp["selector"])
        if price is None:
            continue

        key = f"{comp['name']}_{comp['service']}"

        # Сравниваем с предыдущей ценой
        if key in history:
            prev_price = history[key]["price"]
            if price < prev_price:
                diff = prev_price - price
                alerts.append(
                    f"📉 <b>{comp['name']}</b> снизил цену!\n"
                    f"   {comp['service']}: {prev_price:,} → {price:,} ₽ (-{diff:,})"
                )
            elif price > prev_price:
                diff = price - prev_price
                alerts.append(
                    f"📈 <b>{comp['name']}</b> повысил цену\n"
                    f"   {comp['service']}: {prev_price:,} → {price:,} ₽ (+{diff:,})"
                )

        # Сравниваем с нашей ценой
        my_price = MY_PRICES.get(comp["service"])
        if my_price and price < my_price:
            alerts.append(
                f"⚠️ <b>{comp['name']}</b> дешевле нас!\n"
                f"   {comp['service']}: они {price:,} ₽ vs наши {my_price:,} ₽"
            )

        # Сохраняем
        history[key] = {"price": price, "date": today}

    save_history(history)
    return alerts


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})


if __name__ == "__main__":
    print(f"🔍 Проверяю цены... ({datetime.now().strftime('%H:%M')})")
    alerts = check_prices()

    if alerts:
        text = "🔔 <b>Мониторинг цен</b>\n\n" + "\n\n".join(alerts)
        send_telegram(text)
        print(f"⚡ Найдено {len(alerts)} изменений, алерт отправлен")
    else:
        print("✅ Изменений нет")
