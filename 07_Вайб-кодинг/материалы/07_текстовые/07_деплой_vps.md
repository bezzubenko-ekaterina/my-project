# Деплой проекта на VPS-сервер

> Пошаговая инструкция: как перенести проект с компьютера на сервер.
> Источник: вебинар Андрея Погорелого (Нейроцех)

---

## Зачем нужен сервер

Проект на твоём компьютере работает, пока компьютер включён. Закрыл ноутбук — бот/сайт/приложение остановилось. Сервер работает 24/7.

---

## Шаг 1: Арендуй VPS

| Хостинг | Цена | Плюсы | Минусы |
|---------|------|-------|--------|
| **Timeweb** | от 300₽/мес | Русский интерфейс, поддержка | Зарубежные API блокируют |
| **Beget** | от 200₽/мес | Дёшево | Ограниченные тарифы |
| **Digital Ocean** | от $4/мес | Зарубежные API работают | Нужна зарубежная карта |

Выбирай **Ubuntu 24.04**, минимальный тариф (1 ГБ RAM хватит для бота).

---

## Шаг 2: Попроси Cursor составить план

```
У меня есть проект на Python. Хочу задеплоить на сервер Ubuntu.
Напиши пошаговый план.
```

Cursor выдаст список команд — копируй и выполняй одну за другой.

---

## Шаг 3: Подключись к серверу

В терминале Cursor:
```bash
ssh root@185.xxx.xxx.xxx
```
Пароль — из письма от хостинга.

---

## Шаг 4: Установи Python и зависимости

```bash
apt update && apt install -y python3 python3-pip python3-venv
```

---

## Шаг 5: Перенеси файлы

### Вариант A: через SCP (одной командой)
```bash
scp -r ./my-project/ root@185.xxx.xxx.xxx:/root/
```

### Вариант B: через nano (если один файл)
```bash
nano bot.py
```
Скопируй код из Cursor → вставь → **Ctrl+O** → **Enter** → **Ctrl+X**

### Вариант C: через Git (лучший способ)
```bash
# На компьютере: запушь в GitHub
git push

# На сервере: склонируй
git clone https://github.com/username/my-project.git
cd my-project
```

---

## Шаг 6: Создай виртуальное окружение

```bash
cd /root/my-project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Шаг 7: Создай .env с секретами

```bash
nano .env
```
```
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
OPENAI_API_KEY=sk-...
```

---

## Шаг 8: Настрой автозапуск (systemd)

```bash
nano /etc/systemd/system/mybot.service
```

```ini
[Unit]
Description=My Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/my-project
ExecStart=/root/my-project/venv/bin/python bot.py
Restart=always
RestartSec=10
EnvironmentFile=/root/my-project/.env

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable mybot
systemctl start mybot
```

---

## Полезные команды

```bash
systemctl status mybot        # Статус
systemctl restart mybot       # Перезапустить
systemctl stop mybot          # Остановить
journalctl -u mybot -f        # Логи в реальном времени
journalctl -u mybot --since today  # Логи за сегодня
```

---

## Обновление проекта

### Через Git (рекомендуется):
```bash
cd /root/my-project
git pull
systemctl restart mybot
```

### Вручную:
```bash
nano bot.py     # Отредактируй файл
systemctl restart mybot
```

---

## Для простых сайтов: GitHub Pages (бесплатно)

Если проект — это только HTML/CSS/JS (без сервера):

1. Загрузи файлы на GitHub
2. Settings → Pages → Source: main branch
3. Сайт доступен по ссылке `username.github.io/repo-name`

Подходит для: лендингов, портфолио, HTML-отчётов.

---

## ⚠️ Важно: Россия и зарубежные API

Российские хостинги (Timeweb, Beget) **блокируются** Google, Anthropic, OpenAI.

Если бот обращается к зарубежным AI-сервисам:
- Используй **Digital Ocean** или другой зарубежный хостинг
- Или настрой **VPN/прокси** на российском сервере
