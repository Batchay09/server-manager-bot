import logging
from datetime import datetime
from collections import defaultdict

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from database import db, Server
from utils import format_reminder

logger = logging.getLogger(__name__)


async def check_reminders(bot: Bot):
    """Проверяет серверы и отправляет напоминания пользователям."""
    logger.info("Checking reminders...")

    try:
        users = await db.get_all_users_with_settings()

        for user_settings in users:
            user_id = user_settings.user_id
            days = user_settings.reminder_days

            servers = await db.get_servers_for_reminder(days)
            user_servers = [s for s in servers if s.user_id == user_id]

            if user_servers:
                text = format_reminder(user_servers)
                try:
                    await bot.send_message(user_id, text, parse_mode="HTML")
                    logger.info(f"Sent reminder to user {user_id} for {len(user_servers)} servers")
                except Exception as e:
                    logger.error(f"Failed to send reminder to {user_id}: {e}")

    except Exception as e:
        logger.error(f"Error in check_reminders: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Настраивает и возвращает планировщик."""
    scheduler = AsyncIOScheduler()

    # Проверка напоминаний каждый день в 10:00
    scheduler.add_job(
        check_reminders,
        'cron',
        hour=10,
        minute=0,
        args=[bot],
        id='check_reminders',
        replace_existing=True
    )

    # Также проверяем при запуске
    scheduler.add_job(
        check_reminders,
        'date',
        run_date=datetime.now(),
        args=[bot],
        id='initial_check',
        replace_existing=True
    )

    logger.info("Scheduler configured")
    return scheduler
