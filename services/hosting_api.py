"""
Интеграция с API хостинг-провайдеров.
Поддерживаемые провайдеры: 4VPS.su
"""

import aiohttp
from datetime import datetime, date
from dataclasses import dataclass
from typing import Optional


@dataclass
class HostingServer:
    """Сервер от хостинг-провайдера."""
    external_id: str  # ID на стороне хостинга
    name: str
    ip: Optional[str]
    price: float
    currency: str
    expiry_date: date
    status: str  # active, stopped, expired
    hosting: str  # Название провайдера
    location: Optional[str] = None
    cpu: Optional[int] = None
    ram_gb: Optional[float] = None
    disk_gb: Optional[float] = None


class FourVPSClient:
    """Клиент для работы с API 4VPS.su"""

    BASE_URL = "https://4vps.su/api"
    HOSTING_NAME = "4VPS"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def test_connection(self) -> bool:
        """Проверка валидности API ключа."""
        try:
            servers = await self.get_servers()
            return servers is not None
        except Exception:
            return False

    async def get_servers(self) -> Optional[list[HostingServer]]:
        """Получить список серверов пользователя."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/myservers",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()

                    if not isinstance(data, list):
                        # Возможно API вернул объект с полем data или servers
                        if isinstance(data, dict):
                            data = data.get('data', data.get('servers', []))

                    servers = []
                    for item in data:
                        server = self._parse_server(item)
                        if server:
                            servers.append(server)

                    return servers
        except Exception as e:
            print(f"4VPS API error: {e}")
            return None

    async def get_server_info(self, server_id: str) -> Optional[HostingServer]:
        """Получить детальную информацию о сервере."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/getServerInfo/{server_id}",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()
                    return self._parse_server(data)
        except Exception as e:
            print(f"4VPS API error: {e}")
            return None

    async def extend_server(self, server_id: str) -> bool:
        """Продлить сервер на 1 месяц."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/action/continueServer",
                    headers=self.headers,
                    json={"server_id": server_id},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    return response.status == 200
        except Exception:
            return False

    def _parse_server(self, data: dict) -> Optional[HostingServer]:
        """Парсинг данных сервера из API."""
        try:
            # ID сервера
            server_id = str(data.get('id') or data.get('server_id', ''))
            if not server_id:
                return None

            # Имя сервера
            name = data.get('name') or data.get('hostname') or f"Server {server_id}"

            # IP адрес
            ip = data.get('ip') or data.get('ipv4') or data.get('primary_ip')

            # Цена (в рублях)
            price = float(data.get('price', 0))

            # Дата окончания (Unix timestamp)
            expired = data.get('expired') or data.get('expiry') or data.get('expire_date')
            if expired:
                if isinstance(expired, (int, float)):
                    expiry_date = datetime.fromtimestamp(expired).date()
                elif isinstance(expired, str):
                    # Попытка парсинга строки даты
                    try:
                        expiry_date = datetime.fromisoformat(expired.replace('Z', '+00:00')).date()
                    except ValueError:
                        expiry_date = date.today()
                else:
                    expiry_date = date.today()
            else:
                expiry_date = date.today()

            # Статус
            status_raw = data.get('status', 'unknown')
            if isinstance(status_raw, int):
                status = 'active' if status_raw == 1 else 'stopped'
            else:
                status = str(status_raw).lower()

            # Локация / датацентр
            location = data.get('dc') or data.get('datacenter') or data.get('location')

            # Ресурсы
            cpu = data.get('cpu') or data.get('cores')
            ram = data.get('ram') or data.get('memory')
            disk = data.get('disk') or data.get('storage')

            # Конвертируем RAM из MB в GB если нужно
            if ram and ram > 100:  # Скорее всего в MB
                ram = ram / 1024

            return HostingServer(
                external_id=server_id,
                name=name,
                ip=ip,
                price=price,
                currency="RUB",
                expiry_date=expiry_date,
                status=status,
                hosting=self.HOSTING_NAME,
                location=location,
                cpu=int(cpu) if cpu else None,
                ram_gb=float(ram) if ram else None,
                disk_gb=float(disk) if disk else None
            )
        except Exception as e:
            print(f"Error parsing server data: {e}")
            return None


# Фабрика клиентов для разных провайдеров
def get_hosting_client(provider: str, api_key: str):
    """Получить клиент для конкретного провайдера."""
    providers = {
        "4vps": FourVPSClient,
        "4VPS": FourVPSClient,
    }

    client_class = providers.get(provider)
    if client_class:
        return client_class(api_key)

    raise ValueError(f"Unknown hosting provider: {provider}")
