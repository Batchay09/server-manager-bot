# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Telegram bot for server payment tracking and monitoring. Built with aiogram 3.x (async Telegram Bot framework) and SQLite database.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

## Architecture

### Entry Point
- `bot.py` - Initializes bot, dispatcher, database, scheduler, and monitoring service

### Core Modules
- `config.py` - Environment variables and default settings (BOT_TOKEN, DATABASE_PATH, monitoring intervals)
- `database.py` - SQLite database with aiosqlite. Contains `Server` and `UserSettings` dataclasses, `Database` class with all CRUD operations
- `keyboards.py` - Inline keyboard builders with emoji icons for all bot menus
- `utils.py` - Formatting functions with premium styling (progress bars, color status indicators, card layouts)

### Handlers (`handlers/`)
- `servers.py` - Main router with FSM states for adding/editing servers. Handles commands: /start, /add, /list, /expiring, /settings, /help
- `stats.py` - Statistics command handler (/stats)

### Services (`services/`)
- `scheduler.py` - APScheduler for daily payment reminders (runs at 10:00 and on startup)
- `monitoring.py` - Background service checking server availability via HTTP/TCP, notifies on status changes

### State Machine
`AddServerStates` and `EditServerStates` in `handlers/servers.py` manage multi-step forms using aiogram FSM.

### Database Schema
Two tables: `servers` (id, user_id, name, hosting, location, ip, url, expiry_date, price, currency, payment_period, notes, tags, is_monitoring) and `settings` (user_id, reminder_days, reminder_time).

## Configuration

Copy `.env.example` to `.env` and set `BOT_TOKEN` from @BotFather.

## UI Design

Premium business style with visual elements:
- **Status indicators**: 🟢 (>14d) 🟡 (8-14d) 🟠 (4-7d) 🔴 (<3d/overdue)
- **Progress bars**: `▓▓▓▓▓░░░░░ 50%` for days until payment
- **Card layouts**: Bordered blocks with separators (┌─├─└)
- **Button icons**: ➕📋⚡📊⚙️✅✏️🗑📡
- **Currency flags**: 🇷🇺 RUB, 🇺🇸 USD, 🇪🇺 EUR

Helper functions in `utils.py`:
- `get_status_emoji(days_left)` - returns color indicator
- `get_status_text(days_left)` - returns status text
- `get_progress_bar(days_left, max_days)` - returns visual bar

## Deployment

**Production VPS**: `155.212.144.230` (Beget, Ubuntu 24.04)
- Путь: `/opt/server-manager-bot/`
- Сервис: `systemctl status server-bot`
- Автозапуск: включён через systemd

**Команды на сервере**:
```bash
# Логи
journalctl -u server-bot -f

# Перезапуск
systemctl restart server-bot

# Обновление
cd /opt/server-manager-bot && git pull && systemctl restart server-bot
```

**GitHub**: https://github.com/Batchay09/server-manager-bot

## Current Work / Notes

<!-- Обновляй этот раздел для сохранения контекста между сессиями -->

**Статус проекта**: Production — бот работает 24/7 на VPS
- Добавление/редактирование/удаление серверов
- Напоминания об оплате (APScheduler, ежедневно в 10:00)
- Мониторинг доступности серверов (HTTP/TCP)
- Статистика расходов по валютам и хостингам
- Премиум визуальный стиль с эмодзи и прогресс-барами
- Деплой на VPS с автозапуском
- Умный ввод: выбор из существующих хостингов/локаций/цен
- Поле локации для серверов
- Сортировка списка (по дате, хостингу, локации)

**Telegram**: @Ruulitbot

**Последние изменения**:
- 18.01.2026: Оптимизация ввода (выбор из существующих значений), поле локации, сортировка списка
- 16.01.2026: Деплой на VPS (155.212.144.230), systemd сервис
- 16.01.2026: UI redesign — премиум стиль, эмодзи, прогресс-бары, карточки
- 15.01.2026: Инициализация проекта, создан CLAUDE.md
