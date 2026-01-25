import logging
import asyncio
from typing import Dict

import aiohttp
from aiogram import Bot

from database import db, Server
from config import MONITORING_INTERVAL_MINUTES, MONITORING_TIMEOUT_SECONDS
from security import is_safe_url, is_safe_ip_for_monitoring

logger = logging.getLogger(__name__)


class MonitoringService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.server_status: Dict[int, bool] = {}  # server_id -> is_online
        self.running = False
        self._task = None

    async def start(self):
        """Запускает мониторинг."""
        if self.running:
            return
        self.running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info("Monitoring service started")

    async def stop(self):
        """Останавливает мониторинг."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoring service stopped")

    async def _monitoring_loop(self):
        """Основной цикл мониторинга."""
        while self.running:
            try:
                await self._check_all_servers()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            await asyncio.sleep(MONITORING_INTERVAL_MINUTES * 60)

    async def _check_all_servers(self):
        """Проверяет все серверы с включённым мониторингом."""
        servers = await db.get_servers_for_monitoring()
        logger.info(f"Checking {len(servers)} servers")

        for server in servers:
            is_online = await self._check_server(server)
            prev_status = self.server_status.get(server.id)

            if prev_status is not None and prev_status != is_online:
                # Статус изменился
                await self._notify_status_change(server, is_online)

            self.server_status[server.id] = is_online

    async def _check_server(self, server: Server) -> bool:
        """Проверяет доступность сервера."""
        if server.url:
            # Проверка безопасности URL
            is_safe, _ = is_safe_url(server.url)
            if not is_safe:
                logger.warning(f"Skipping unsafe URL for server {server.id}: {server.url}")
                return False
            return await self._check_url(server.url)
        elif server.ip:
            # Проверка безопасности IP
            is_safe, _ = is_safe_ip_for_monitoring(server.ip)
            if not is_safe:
                logger.warning(f"Skipping unsafe IP for server {server.id}: {server.ip}")
                return False
            return await self._check_ip(server.ip)
        return False

    async def _check_url(self, url: str) -> bool:
        """Проверяет доступность URL."""
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'

        try:
            timeout = aiohttp.ClientTimeout(total=MONITORING_TIMEOUT_SECONDS)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    return response.status < 500
        except Exception as e:
            logger.debug(f"URL check failed for {url}: {e}")
            return False

    async def _check_ip(self, ip: str) -> bool:
        """Проверяет доступность IP (TCP connect на порт 80 или 443)."""
        for port in [443, 80, 22]:
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port),
                    timeout=MONITORING_TIMEOUT_SECONDS
                )
                writer.close()
                await writer.wait_closed()
                return True
            except Exception:
                continue
        return False

    async def _notify_status_change(self, server: Server, is_online: bool):
        """Отправляет уведомление об изменении статуса."""
        if is_online:
            status = "🟢 ОНЛАЙН"
            header = "✅ Сервер снова доступен"
        else:
            status = "🔴 НЕДОСТУПЕН"
            header = "⚠️ Сервер недоступен"

        text = (
            f"┌{'─' * 26}\n"
            f"│ {header}\n"
            f"├{'─' * 26}\n"
            f"│ 🖥 <b>{server.name}</b>\n"
            f"│ 🏢 {server.hosting}\n"
            f"│ 📡 Статус: {status}\n"
        )

        if server.ip:
            text += f"│ 🌐 <code>{server.ip}</code>\n"
        if server.url:
            text += f"│ 🔗 {server.url}\n"

        text += f"└{'─' * 26}"

        try:
            await self.bot.send_message(server.user_id, text, parse_mode="HTML")
            logger.info(f"Sent status notification for server {server.id} to user {server.user_id}")
        except Exception as e:
            logger.error(f"Failed to send status notification: {e}")
