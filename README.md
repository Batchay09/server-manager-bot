# 🖥 Server Manager Bot

Telegram-бот для отслеживания оплаты серверов и мониторинга их доступности.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![aiogram](https://img.shields.io/badge/aiogram-3.x-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Возможности

- 📋 **Управление серверами** — добавление, редактирование, удаление
- 🔔 **Напоминания об оплате** — автоматические уведомления за N дней
- 📡 **Мониторинг доступности** — проверка HTTP/TCP с уведомлениями
- 📊 **Статистика расходов** — по валютам и хостингам
- 🎨 **Премиум UI** — цветные статусы, прогресс-бары, карточки

## 🚀 Быстрый старт

### Требования
- Python 3.11+
- Telegram Bot Token от [@BotFather](https://t.me/BotFather)

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/Batchay09/server-manager-bot.git
cd server-manager-bot

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt

# Настроить переменные окружения
cp .env.example .env
# Отредактировать .env и добавить BOT_TOKEN
```

### Запуск

```bash
python bot.py
```

## 📱 Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/add` | Добавить сервер |
| `/list` | Список серверов |
| `/expiring` | Серверы с истекающей оплатой |
| `/stats` | Статистика расходов |
| `/settings` | Настройки напоминаний |
| `/help` | Справка |

## 🎨 Интерфейс

### Статусы оплаты
- 🟢 Более 14 дней
- 🟡 8-14 дней
- 🟠 4-7 дней
- 🔴 Менее 3 дней / Просрочено

### Карточка сервера
```
┌────────────────────────────
│ 🖥 Production API
├────────────────────────────
│ 🏢 Hetzner
│ 📅 До 25.02.2026 (41 дн.)
│ ▓▓▓▓▓▓▓▓░░ 80% 🟢
│ 💰 29.99 EUR/мес
├────────────────────────────
│ 🌐 185.16.32.11
│ 📡 Мониторинг: 🟢 Вкл
└────────────────────────────
```

## 🏗 Архитектура

```
server_bot/
├── bot.py              # Точка входа
├── config.py           # Конфигурация
├── database.py         # SQLite + aiosqlite
├── keyboards.py        # Inline-клавиатуры
├── utils.py            # Форматирование
├── handlers/
│   ├── servers.py      # Основные хендлеры
│   └── stats.py        # Статистика
└── services/
    ├── scheduler.py    # Напоминания (APScheduler)
    └── monitoring.py   # Мониторинг доступности
```

## ⚙️ Конфигурация

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `BOT_TOKEN` | Токен Telegram бота | — |
| `DATABASE_PATH` | Путь к SQLite базе | `servers.db` |

## 📝 Лицензия

MIT License — свободное использование и модификация.

## 👤 Автор

Создано с помощью [Claude Code](https://claude.ai/code)
