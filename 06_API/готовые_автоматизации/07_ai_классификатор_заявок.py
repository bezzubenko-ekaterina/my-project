"""
AI-классификатор заявок — принимает текст, AI определяет категорию и приоритет.
Курс АССИСТ+

Что делает:
- Получает текст заявки
- AI (Claude/OpenAI) определяет: категорию, приоритет, извлекает контакты
- Возвращает структурированные данные (JSON)
- Можно встроить в бота или автоматизацию

Зависимости: pip install anthropic python-dotenv
"""

import os
import json
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ========== НАСТРОЙ ПОД СЕБЯ ==========
CATEGORIES = [
    "Подбор ассистента",
    "Обучение",
    "Аудит процессов",
    "Курс Cursor AI",
    "Партнёрство",
    "Другое",
]

PRIORITIES = ["Высокий", "Средний", "Низкий"]
# =======================================


def classify(text: str) -> dict:
    """Классифицирует заявку через AI."""
    prompt = f"""Проанализируй текст заявки клиента и верни JSON:

Текст заявки:
---
{text}
---

Категории: {', '.join(CATEGORIES)}
Приоритеты: {', '.join(PRIORITIES)}

Верни ТОЛЬКО JSON (без комментариев):
{{
  "name": "имя клиента (если есть)",
  "phone": "телефон (если есть)",
  "email": "email (если есть)",
  "category": "одна из категорий",
  "priority": "один из приоритетов",
  "summary": "краткое описание заявки (1 предложение)",
  "sentiment": "позитивный/нейтральный/негативный"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        result = json.loads(response.content[0].text)
    except json.JSONDecodeError:
        result = {
            "name": "Не определено",
            "category": "Другое",
            "priority": "Средний",
            "summary": text[:100],
            "sentiment": "нейтральный",
        }

    return result


# --- Примеры ---
if __name__ == "__main__":
    test_messages = [
        "Здравствуйте! Меня зовут Анна, телефон +7 999 123 45 67. "
        "Ищу ассистента для интернет-магазина. Нужен человек с опытом "
        "работы с Wildberries и Ozon. Бюджет до 60 000. Срочно!",

        "Добрый день. Хотели бы обучить команду из 5 человек работе "
        "с AI-инструментами. Формат — корпоративный, 2 дня. "
        "Контакт: ivan@company.ru",

        "Привет, а у вас есть курс по Cursor? Сколько стоит? "
        "Можно в рассрочку?",
    ]

    for i, msg in enumerate(test_messages, 1):
        print(f"\n{'='*50}")
        print(f"Заявка #{i}: {msg[:60]}...")
        result = classify(msg)
        print(json.dumps(result, ensure_ascii=False, indent=2))
