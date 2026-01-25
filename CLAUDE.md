# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Telegram bot for server payment tracking and monitoring. Built with aiogram 3.x (async Telegram Bot framework) and SQLite database.

## Commands

```bash
pip install -r requirements.txt  # Install dependencies
python bot.py                    # Run the bot
```

## Architecture

### Entry Point
`bot.py` — Initializes bot, dispatcher, database, scheduler, and monitoring service.

### Core Modules
- `config.py` — Environment variables (BOT_TOKEN, DATABASE_PATH) and currency rates (USD_RATE, EUR_RATE)
- `database.py` — SQLite with aiosqlite. `Server` and `UserSettings` dataclasses, `Database` class with CRUD
- `keyboards.py` — Inline keyboard builders with emoji icons
- `utils.py` — Formatting functions (progress bars, status indicators, card layouts, currency conversion)

### Handlers (`handlers/`)
- `servers.py` — Main router with FSM states (`AddServerStates`, `EditServerStates`, `PaymentStates`). Commands: /start, /add, /list, /expiring, /settings, /help
- `stats.py` — Statistics handler (/stats)

### Services (`services/`)
- `scheduler.py` — APScheduler for daily reminders (10:00 + startup)
- `monitoring.py` — Background HTTP/TCP availability checks with notifications

### Database Schema
- `servers`: id, user_id, name, hosting, location, ip, url, expiry_date, price, currency, payment_period, notes, tags, is_monitoring
- `settings`: user_id, reminder_days, reminder_time

## Configuration

Copy `.env.example` to `.env` and set `BOT_TOKEN` from @BotFather.

## Быстрые команды

**"деплой"** — залить на VPS:
```bash
source .env && export SSHPASS="$VPS_PASS" && sshpass -e ssh $VPS_USER@$VPS_HOST "cd /opt/server-manager-bot && git pull && systemctl restart server-bot"
```

**"релиз"** — полный цикл выпуска (обязательно при коммите):
1. Инкремент VERSION (semver: MAJOR/MINOR/PATCH)
2. Добавить раздел в CHANGELOG.md
3. Git commit + push
4. Deploy на VPS

## Git Workflow

При коммите **ВСЕГДА**:

1. **VERSION** — инкремент по semver
2. **CHANGELOG.md** — новый раздел `## [X.X.X] - YYYY-MM-DD`
3. **Commit** с префиксом: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
4. **Push** + **Deploy**

## UI Design

- **Status indicators**: 🟢 (>14d) 🟡 (8-14d) 🟠 (4-7d) 🔴 (<3d/overdue)
- **Progress bars**: `▓▓▓▓▓░░░░░ 50%`
- **Card layouts**: Bordered blocks (┌─├─└)
- **Currency flags**: 🇷🇺 RUB, 🇺🇸 USD, 🇪🇺 EUR

Key functions in `utils.py`: `get_status_emoji()`, `get_status_text()`, `get_progress_bar()`, `convert_to_rub()`

## Deployment

**VPS**: `155.212.144.230` | Path: `/opt/server-manager-bot/` | Service: `server-bot`

```bash
journalctl -u server-bot -f     # Logs
systemctl restart server-bot    # Restart
```

## Notes

**Telegram**: @Ruulitbot
**GitHub**: https://github.com/Batchay09/server-manager-bot
**Status**: Production (24/7 on VPS)
