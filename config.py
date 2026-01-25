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

# Курсы валют к рублю
EXCHANGE_RATES = {
    "RUB": 1.0,
    "USD": 83.0,
    "EUR": 91.0,
}

# === БЕЗОПАСНОСТЬ ===

# Ключ шифрования API ключей (32 байта в base64)
# Сгенерировать: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

# Разрешённые пользователи (пустой список = все разрешены)
# Формат: "123456,789012,345678"
ALLOWED_USERS = [int(x) for x in os.getenv("ALLOWED_USERS", "").split(",") if x.strip()]

# Лимиты
MAX_SERVERS_PER_USER = int(os.getenv("MAX_SERVERS_PER_USER", "100"))
RATE_LIMIT_SECONDS = float(os.getenv("RATE_LIMIT_SECONDS", "0.5"))  # Минимум между сообщениями
