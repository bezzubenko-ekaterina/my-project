"""
AI-генератор текстов — посты, письма, описания за секунды.
Курс АССИСТ+

Что делает:
- Генерирует тексты по шаблонам: пост для Telegram, email, описание вакансии
- Использует AI (Claude) с подробными промптами
- Сохраняет результат в файл
- Можно встроить в бота или запускать из терминала

Зависимости: pip install anthropic python-dotenv
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ========== НАСТРОЙ ПОД СЕБЯ ==========
COMPANY = "АССИСТ+"
COMPANY_DESC = "HR-агентство по подбору бизнес-ассистентов для предпринимателей"
TONE = "дружелюбный, профессиональный, без воды"
# =======================================


TEMPLATES = {
    "telegram_post": {
        "name": "Пост для Telegram-канала",
        "prompt": (
            "Напиши пост для Telegram-канала компании {company} ({desc}).\n"
            "Тема: {topic}\n\n"
            "Требования:\n"
            "- Длина: 500-800 символов\n"
            "- Тон: {tone}\n"
            "- Начни с цепляющего заголовка (жирным)\n"
            "- Используй эмодзи уместно (2-4 штуки)\n"
            "- Заверши призывом к действию\n"
            "- Добавь 2-3 хештега\n"
            "- Форматирование: HTML (bold, italic)"
        ),
    },
    "email_cold": {
        "name": "Холодное письмо",
        "prompt": (
            "Напиши холодное email-письмо от {company} ({desc}).\n"
            "Кому: {topic}\n\n"
            "Требования:\n"
            "- Тема письма: короткая, интригующая (до 50 символов)\n"
            "- Длина: 150-250 слов\n"
            "- Тон: {tone}\n"
            "- Начни с чего-то персонального\n"
            "- Одно конкретное предложение\n"
            "- Чёткий CTA (призыв к действию)\n"
            "- Подпись: Имя, должность, контакты"
        ),
    },
    "vacancy": {
        "name": "Описание вакансии",
        "prompt": (
            "Напиши описание вакансии для {company} ({desc}).\n"
            "Позиция: {topic}\n\n"
            "Структура:\n"
            "- Заголовок вакансии\n"
            "- О компании (2 предложения)\n"
            "- Чем предстоит заниматься (5-7 пунктов)\n"
            "- Что мы ожидаем (5-7 пунктов)\n"
            "- Что предлагаем (5-7 пунктов, включая зарплатную вилку)\n"
            "- Как откликнуться\n\n"
            "Тон: {tone}\n"
            "Язык: русский"
        ),
    },
    "social_post": {
        "name": "Пост для соцсетей",
        "prompt": (
            "Напиши пост для Instagram/VK от {company} ({desc}).\n"
            "Тема: {topic}\n\n"
            "Требования:\n"
            "- Длина: 300-500 символов\n"
            "- Тон: {tone}, живой\n"
            "- Начни с вопроса или истории\n"
            "- Дай пользу (совет, лайфхак, факт)\n"
            "- Заверши вопросом к аудитории\n"
            "- 3-5 хештегов"
        ),
    },
    "reply_review": {
        "name": "Ответ на отзыв",
        "prompt": (
            "Напиши ответ на отзыв клиента от имени {company} ({desc}).\n"
            "Отзыв: {topic}\n\n"
            "Требования:\n"
            "- Если позитивный: поблагодари искренне, без шаблонов\n"
            "- Если негативный: извинись, предложи решение, дай контакт\n"
            "- Тон: {tone}\n"
            "- Длина: 50-150 слов\n"
            "- Обратись по имени, если оно есть в отзыве"
        ),
    },
}


def generate(template_key: str, topic: str) -> str:
    template = TEMPLATES[template_key]
    prompt = template["prompt"].format(
        company=COMPANY,
        desc=COMPANY_DESC,
        topic=topic,
        tone=TONE,
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


if __name__ == "__main__":
    print("📝 AI-генератор текстов\n")
    print("Доступные шаблоны:")
    for key, tpl in TEMPLATES.items():
        print(f"  {key} — {tpl['name']}")

    print("\nИспользование:")
    print('  python 09_ai_генератор_текстов.py telegram_post "5 ошибок при найме ассистента"')
    print('  python 09_ai_генератор_текстов.py email_cold "предприниматели с оборотом от 5 млн"')
    print('  python 09_ai_генератор_текстов.py vacancy "бизнес-ассистент на удалёнке"')

    if len(sys.argv) >= 3:
        template_key = sys.argv[1]
        topic = " ".join(sys.argv[2:])

        if template_key not in TEMPLATES:
            print(f"\n❌ Шаблон '{template_key}' не найден")
        else:
            print(f"\n⏳ Генерирую: {TEMPLATES[template_key]['name']}...")
            result = generate(template_key, topic)

            print(f"\n{'='*50}")
            print(result)
            print(f"{'='*50}")

            # Сохраняем
            os.makedirs("generated", exist_ok=True)
            filename = f"generated/{template_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w") as f:
                f.write(result)
            print(f"\n💾 Сохранено: {filename}")
