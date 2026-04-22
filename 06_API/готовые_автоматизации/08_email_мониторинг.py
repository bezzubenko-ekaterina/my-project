"""
Мониторинг email — проверяет почту, шлёт алерт в Telegram о новых письмах.
Курс АССИСТ+

Что делает:
- Подключается к Gmail по IMAP
- Проверяет непрочитанные письма
- Отправляет сводку в Telegram
- Фильтрует по отправителям (VIP-список)

Запуск: crontab -e → */30 * * * * python 08_email_мониторинг.py (каждые 30 мин)
Зависимости: pip install python-dotenv requests

Настройка Gmail:
1. Включи IMAP: Gmail → Settings → See all settings → Forwarding and POP/IMAP → Enable IMAP
2. Создай App Password: Google Account → Security → 2-Step Verification → App passwords
"""

import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ========== НАСТРОЙ ПОД СЕБЯ ==========
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")      # your@gmail.com
EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")  # App Password (не основной пароль!)
IMAP_SERVER = "imap.gmail.com"

# VIP-отправители (всегда уведомлять)
VIP_SENDERS = [
    "boss@company.com",
    "client@important.com",
]

MAX_EMAILS = 5  # Максимум писем в сводке
# =======================================


def decode_mime(text):
    """Декодирует MIME-заголовок."""
    if text is None:
        return ""
    parts = decode_header(text)
    result = ""
    for part, charset in parts:
        if isinstance(part, bytes):
            result += part.decode(charset or "utf-8", errors="ignore")
        else:
            result += part
    return result


def check_email():
    """Проверяет непрочитанные письма."""
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    mail.select("inbox")

    # Ищем непрочитанные
    status, messages = mail.search(None, "UNSEEN")
    if status != "OK":
        return []

    msg_ids = messages[0].split()
    if not msg_ids:
        return []

    emails = []
    for msg_id in msg_ids[-MAX_EMAILS:]:  # Последние N
        status, msg_data = mail.fetch(msg_id, "(RFC822)")
        if status != "OK":
            continue

        msg = email.message_from_bytes(msg_data[0][1])
        sender = decode_mime(msg["From"])
        subject = decode_mime(msg["Subject"]) or "(без темы)"
        date = msg["Date"]

        is_vip = any(vip in sender.lower() for vip in VIP_SENDERS)

        emails.append({
            "sender": sender,
            "subject": subject,
            "date": date,
            "vip": is_vip,
        })

    mail.logout()
    return emails


def format_notification(emails):
    if not emails:
        return None

    vip = [e for e in emails if e["vip"]]
    regular = [e for e in emails if not e["vip"]]

    text = f"📧 <b>Новые письма: {len(emails)}</b>\n\n"

    if vip:
        text += "⭐ <b>VIP:</b>\n"
        for e in vip:
            text += f"  📩 {e['sender'][:40]}\n     {e['subject'][:50]}\n\n"

    if regular:
        text += "📬 <b>Остальные:</b>\n"
        for e in regular:
            text += f"  • {e['subject'][:50]}\n    от {e['sender'][:30]}\n"

    return text


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})


if __name__ == "__main__":
    emails = check_email()
    notification = format_notification(emails)

    if notification:
        send_telegram(notification)
        print(f"✅ Найдено {len(emails)} новых писем, уведомление отправлено")
    else:
        print("📭 Новых писем нет")
