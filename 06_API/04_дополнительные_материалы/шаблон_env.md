# Шаблон .env файла

> Создай файл `.env` в корне проекта. Cursor подхватит переменные.
> НИКОГДА не коммить `.env` в git! Добавь его в `.gitignore`.

## Что такое .env

Обычный текстовый файл в корне проекта, где хранятся секретные ключи. Каждая строка — одна настройка в формате `НАЗВАНИЕ=значение`. Файл лежит в папке проекта, но **не загружается** в GitHub (если `.gitignore` настроен правильно).

## Пример

```env
# === Telegram ===
TELEGRAM_BOT_TOKEN=1234567890:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=775745451

# === Google Sheets ===
GOOGLE_SHEETS_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
GOOGLE_SERVICE_ACCOUNT=path/to/credentials.json

# === База данных ===
DATABASE_URL=sqlite:///data.db

# === Почта ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# === Разное ===
DEBUG=false
TIMEZONE=Europe/Moscow
```

## .gitignore — добавь это:

```
.env
.env.local
*.db
__pycache__/
.venv/
credentials.json
```

## Дополнительно: API нейросетей

Если захотите подключить AI-модели напрямую (не через Cursor), добавьте соответствующие ключи:

```env
# === AI модели (опционально) ===
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIza...
```

Но в основном курсе мы работаем через Cursor — эти ключи не нужны.
