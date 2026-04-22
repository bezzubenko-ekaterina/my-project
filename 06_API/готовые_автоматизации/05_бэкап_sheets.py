"""
Бэкап Google Sheets → локальные CSV + JSON файлы.
Курс АССИСТ+

Что делает:
- Скачивает все листы из Google Таблицы
- Сохраняет в CSV и JSON форматах
- Хранит историю бэкапов (по дате)
- Уведомляет в Telegram о результате

Запуск: crontab -e → 0 23 * * * python 05_бэкап_sheets.py
Зависимости: pip install gspread python-dotenv requests
"""

import os
import csv
import json
from datetime import datetime
from dotenv import load_dotenv
import requests

try:
    import gspread
except ImportError:
    print("Установи: pip install gspread")
    exit(1)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ========== НАСТРОЙ ПОД СЕБЯ ==========
SPREADSHEET_NAME = "Заявки АССИСТ+"  # Название таблицы
CREDENTIALS_FILE = "credentials.json"
BACKUP_DIR = "backups"
# =======================================


def backup():
    gc = gspread.service_account(filename=CREDENTIALS_FILE)
    sh = gc.open(SPREADSHEET_NAME)

    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    backup_path = f"{BACKUP_DIR}/{date_str}"
    os.makedirs(backup_path, exist_ok=True)

    results = []
    for worksheet in sh.worksheets():
        name = worksheet.title
        data = worksheet.get_all_records()
        rows = worksheet.get_all_values()

        # CSV
        csv_file = f"{backup_path}/{name}.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for row in rows:
                writer.writerow(row)

        # JSON
        json_file = f"{backup_path}/{name}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        results.append(f"  📄 {name}: {len(data)} строк")

    return backup_path, results


def send_telegram(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})


if __name__ == "__main__":
    try:
        path, results = backup()
        text = (
            f"💾 <b>Бэкап Google Sheets</b>\n\n"
            f"📁 {path}\n\n" +
            "\n".join(results) +
            f"\n\n✅ Успешно!"
        )
        print(text.replace("<b>", "").replace("</b>", ""))
        send_telegram(text)
    except Exception as e:
        error_text = f"❌ Ошибка бэкапа: {e}"
        print(error_text)
        send_telegram(error_text)
