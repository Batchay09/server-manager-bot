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
- `keyboards.py` - Inline keyboard builders for all bot menus
- `utils.py` - Formatting functions (server info, lists, stats, reminders) and date/price parsers

### Handlers (`handlers/`)
- `servers.py` - Main router with FSM states for adding/editing servers. Handles commands: /start, /add, /list, /expiring, /settings, /help
- `stats.py` - Statistics command handler (/stats)

### Services (`services/`)
- `scheduler.py` - APScheduler for daily payment reminders (runs at 10:00 and on startup)
- `monitoring.py` - Background service checking server availability via HTTP/TCP, notifies on status changes

### State Machine
`AddServerStates` and `EditServerStates` in `handlers/servers.py` manage multi-step forms using aiogram FSM.

### Database Schema
Two tables: `servers` (id, user_id, name, hosting, ip, url, expiry_date, price, currency, payment_period, notes, tags, is_monitoring) and `settings` (user_id, reminder_days, reminder_time).

## Configuration

Copy `.env.example` to `.env` and set `BOT_TOKEN` from @BotFather.

## Current Work / Notes

<!-- Обновляй этот раздел для сохранения контекста между сессиями -->

**Статус проекта**: Базовая функциональность готова
- Добавление/редактирование/удаление серверов
- Напоминания об оплате (APScheduler, ежедневно в 10:00)
- Мониторинг доступности серверов (HTTP/TCP)
- Статистика расходов по валютам и хостингам

**Последние изменения**:
- 15.01.2026: Инициализация проекта, создан CLAUDE.md
