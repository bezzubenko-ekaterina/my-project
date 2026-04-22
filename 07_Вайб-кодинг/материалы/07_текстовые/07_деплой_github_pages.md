# Деплой на GitHub Pages — пошагово

## Что нужно
- Аккаунт на github.com
- Git установлен (Cursor делает это за тебя)
- Проект с index.html в корне

## Шаг 1. Создай репозиторий

1. Открой github.com → New repository
2. Название: `my-landing` (или любое)
3. Public (бесплатно)
4. Не ставь галочки (README, .gitignore) — у тебя уже есть файлы
5. Create repository

## Шаг 2. Подключи и запуш

В терминале Cursor (Ctrl+`):

```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/ТВОЙ_USERNAME/my-landing.git
git push -u origin main
```

## Шаг 3. Включи Pages

1. Открой репозиторий на GitHub
2. Settings → Pages (в левом меню)
3. Source: **Deploy from a branch**
4. Branch: **main** → **/ (root)**
5. Save

## Шаг 4. Подожди 1-2 минуты

GitHub соберёт сайт. Ссылка появится вверху:

```
https://ТВОЙ_USERNAME.github.io/my-landing/
```

## Обновление

При каждом `git push` сайт обновляется автоматически (через 1-2 минуты).

## Свой домен (опционально)

1. Купи домен (например, на reg.ru)
2. Settings → Pages → Custom domain → введи домен
3. У регистратора: добавь CNAME запись → ТВОЙ_USERNAME.github.io

## Ограничения

- Только статические сайты (HTML/CSS/JS)
- Нет серверного кода (Python, Node.js)
- Для серверного кода → Vercel или VPS

---

*© АССИСТ+*
