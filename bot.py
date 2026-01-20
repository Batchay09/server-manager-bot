import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import init_db
from handlers import servers_router, stats_router, hosting_router
from services.scheduler import setup_scheduler
from services.monitoring import MonitoringService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found! Create .env file with BOT_TOKEN=your_token")
        sys.exit(1)

    # Инициализация БД
    await init_db()
    logger.info("Database initialized")

    # Создание бота и диспетчера
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(servers_router)
    dp.include_router(stats_router)
    dp.include_router(hosting_router)

    # Настройка планировщика напоминаний
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started")

    # Запуск мониторинга
    monitoring = MonitoringService(bot)
    await monitoring.start()
    logger.info("Monitoring service started")

    try:
        logger.info("Bot starting...")
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await monitoring.stop()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
