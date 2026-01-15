import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_PATH = os.getenv("DATABASE_PATH", "servers.db")

# Настройки по умолчанию
DEFAULT_REMINDER_DAYS = 7
DEFAULT_REMINDER_TIME = "10:00"
MONITORING_INTERVAL_MINUTES = 5
MONITORING_TIMEOUT_SECONDS = 10
