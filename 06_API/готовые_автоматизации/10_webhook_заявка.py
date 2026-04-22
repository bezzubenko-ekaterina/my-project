"""
Webhook-приёмник заявок — принимает данные с сайта → Telegram + JSON.
Курс АССИСТ+

Что делает:
- Поднимает мини-сервер на порту 8080
- Принимает POST-запросы с формы сайта
- Сохраняет заявку в JSON
- Уведомляет в Telegram

На сайте: форма отправляет POST на http://your-server:8080/webhook

Зависимости: pip install flask python-dotenv requests
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
import requests

try:
    from flask import Flask, request, jsonify
except ImportError:
    print("Установи: pip install flask")
    exit(1)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = Flask(__name__)
LEADS_FILE = "leads.json"

# ========== НАСТРОЙ ПОД СЕБЯ ==========
ALLOWED_ORIGINS = ["*"]  # Или укажи домен сайта: ["https://example.com"]
# =======================================


def load_leads():
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE) as f:
            return json.load(f)
    return []


def save_lead(lead):
    leads = load_leads()
    leads.append(lead)
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)


def notify_telegram(lead):
    text = (
        f"🔔 <b>Новая заявка с сайта!</b>\n\n"
        f"<b>Имя:</b> {lead.get('name', '-')}\n"
        f"<b>Телефон:</b> {lead.get('phone', '-')}\n"
        f"<b>Email:</b> {lead.get('email', '-')}\n"
        f"<b>Сообщение:</b> {lead.get('message', '-')}\n"
        f"<b>Время:</b> {lead.get('date', '-')}\n"
        f"<b>Источник:</b> {lead.get('source', 'сайт')}"
    )
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})


@app.route("/webhook", methods=["POST"])
def webhook():
    """Принимает заявку."""
    data = request.get_json() or request.form.to_dict()

    lead = {
        "name": data.get("name", ""),
        "phone": data.get("phone", ""),
        "email": data.get("email", ""),
        "message": data.get("message", ""),
        "source": data.get("source", "сайт"),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip": request.remote_addr,
    }

    save_lead(lead)
    notify_telegram(lead)

    return jsonify({"status": "ok", "message": "Заявка принята"}), 200


@app.route("/leads", methods=["GET"])
def get_leads():
    """Список заявок (для проверки)."""
    leads = load_leads()
    return jsonify({"total": len(leads), "leads": leads[-20:]})  # Последние 20


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "time": datetime.now().isoformat()})


@app.after_request
def add_cors(response):
    origin = request.headers.get("Origin", "*")
    if ALLOWED_ORIGINS == ["*"] or origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


if __name__ == "__main__":
    print("🌐 Webhook-сервер запущен на http://0.0.0.0:8080")
    print("   POST /webhook — приём заявок")
    print("   GET /leads — список заявок")
    print("   GET /health — проверка")
    print()
    print("Тест: curl -X POST http://localhost:8080/webhook "
          '-H "Content-Type: application/json" '
          '-d \'{"name":"Тест","phone":"+79991234567"}\'')
    app.run(host="0.0.0.0", port=8080, debug=False)
