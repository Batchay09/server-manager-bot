"""
Middleware для безопасности: rate limiting, контроль доступа.
"""

import logging
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from config import ALLOWED_USERS, RATE_LIMIT_SECONDS

logger = logging.getLogger(__name__)


class AccessControlMiddleware(BaseMiddleware):
    """Проверяет, разрешён ли пользователь."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем user_id из события
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        # Если список разрешённых пуст — разрешаем всех
        if ALLOWED_USERS and user_id not in ALLOWED_USERS:
            logger.warning(f"Access denied for user {user_id}")
            if isinstance(event, Message):
                await event.answer(
                    "⛔ Доступ запрещён\n\n"
                    "Этот бот работает в приватном режиме.",
                    parse_mode="HTML"
                )
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Доступ запрещён", show_alert=True)
            return None

        return await handler(event, data)


class RateLimitMiddleware(BaseMiddleware):
    """Ограничивает частоту запросов от пользователя."""

    def __init__(self):
        self.user_last_request: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем user_id
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if user_id:
            now = time.time()
            last_request = self.user_last_request.get(user_id, 0)

            if now - last_request < RATE_LIMIT_SECONDS:
                logger.debug(f"Rate limit hit for user {user_id}")
                if isinstance(event, CallbackQuery):
                    await event.answer("⏳ Подождите немного...", show_alert=False)
                return None

            self.user_last_request[user_id] = now

            # Очистка старых записей (каждые 100 запросов)
            if len(self.user_last_request) > 1000:
                cutoff = now - 60
                self.user_last_request = {
                    uid: ts for uid, ts in self.user_last_request.items()
                    if ts > cutoff
                }

        return await handler(event, data)
