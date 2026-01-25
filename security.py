"""
Модуль безопасности: шифрование, валидация, защита от SSRF.
"""

import ipaddress
import logging
import re
from urllib.parse import urlparse
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from config import ENCRYPTION_KEY

logger = logging.getLogger(__name__)

# === ШИФРОВАНИЕ ===

_fernet: Optional[Fernet] = None


def _get_fernet() -> Optional[Fernet]:
    """Получить инстанс Fernet для шифрования."""
    global _fernet
    if _fernet is None and ENCRYPTION_KEY:
        try:
            _fernet = Fernet(ENCRYPTION_KEY.encode())
        except Exception as e:
            logger.error(f"Invalid ENCRYPTION_KEY: {e}")
    return _fernet


def encrypt_api_key(api_key: str) -> str:
    """Шифрует API ключ. Если шифрование недоступно, возвращает как есть."""
    fernet = _get_fernet()
    if fernet:
        try:
            return fernet.encrypt(api_key.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
    return api_key


def decrypt_api_key(encrypted_key: str) -> str:
    """Расшифровывает API ключ. Если не зашифрован, возвращает как есть."""
    fernet = _get_fernet()
    if fernet:
        try:
            return fernet.decrypt(encrypted_key.encode()).decode()
        except InvalidToken:
            # Ключ не зашифрован (старый формат)
            return encrypted_key
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
    return encrypted_key


# === ВАЛИДАЦИЯ IP ===

def is_valid_ip(ip: str) -> bool:
    """Проверяет, является ли строка валидным IP-адресом."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_private_ip(ip: str) -> bool:
    """Проверяет, является ли IP приватным."""
    try:
        addr = ipaddress.ip_address(ip)
        return (
            addr.is_private or
            addr.is_loopback or
            addr.is_reserved or
            addr.is_link_local
        )
    except ValueError:
        return True  # Недействительный IP считаем опасным


# === ВАЛИДАЦИЯ URL (SSRF защита) ===

# Запрещённые хосты
BLOCKED_HOSTS = {
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '::1',
    'metadata.google.internal',
    '169.254.169.254',  # AWS metadata
}

# Приватные диапазоны IP
PRIVATE_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fc00::/7'),
    ipaddress.ip_network('fe80::/10'),
]


def is_safe_url(url: str) -> tuple[bool, str]:
    """
    Проверяет URL на безопасность (защита от SSRF).
    Возвращает (is_safe, error_message).
    """
    if not url:
        return False, "URL пустой"

    # Добавляем схему если нет
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Некорректный URL"

    # Проверяем схему
    if parsed.scheme not in ('http', 'https'):
        return False, "Разрешены только http/https"

    # Проверяем наличие хоста
    host = parsed.hostname
    if not host:
        return False, "Отсутствует хост"

    # Проверяем заблокированные хосты
    if host.lower() in BLOCKED_HOSTS:
        return False, "Хост заблокирован"

    # Проверяем, не является ли хост IP-адресом из приватного диапазона
    try:
        ip = ipaddress.ip_address(host)
        for network in PRIVATE_RANGES:
            if ip in network:
                return False, "Приватные IP запрещены"
    except ValueError:
        # Это не IP, а доменное имя — OK
        pass

    # Проверяем порт
    port = parsed.port
    if port and port not in (80, 443, 8080, 8443):
        return False, "Разрешены только стандартные порты"

    return True, ""


def is_safe_ip_for_monitoring(ip: str) -> tuple[bool, str]:
    """
    Проверяет IP на безопасность для мониторинга.
    Возвращает (is_safe, error_message).
    """
    if not ip:
        return False, "IP пустой"

    if not is_valid_ip(ip):
        return False, "Некорректный IP адрес"

    if is_private_ip(ip):
        return False, "Приватные IP запрещены для мониторинга"

    return True, ""


# === ВАЛИДАЦИЯ ВВОДА ===

def sanitize_text(text: str, max_length: int = 500) -> str:
    """Очищает текст от потенциально опасных символов."""
    if not text:
        return ""
    # Убираем HTML теги (кроме разрешённых Telegram)
    text = re.sub(r'<(?!/?(?:b|i|u|s|code|pre|a)\b)[^>]*>', '', text)
    # Ограничиваем длину
    return text[:max_length].strip()
