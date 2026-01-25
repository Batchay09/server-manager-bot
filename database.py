import aiosqlite
from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass

from config import DATABASE_PATH, MAX_SERVERS_PER_USER
from security import encrypt_api_key, decrypt_api_key


@dataclass
class Server:
    id: int
    user_id: int
    name: str
    hosting: str
    location: Optional[str]
    ip: Optional[str]
    url: Optional[str]
    expiry_date: date
    price: float
    currency: str
    payment_period: str
    notes: Optional[str]
    tags: Optional[str]
    is_monitoring: bool
    created_at: datetime


@dataclass
class UserSettings:
    user_id: int
    reminder_days: int
    reminder_time: str


@dataclass
class HostingAPIKey:
    id: int
    user_id: int
    provider: str  # 4vps, hetzner, etc.
    api_key: str
    created_at: datetime


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                hosting TEXT NOT NULL,
                location TEXT,
                ip TEXT,
                url TEXT,
                expiry_date DATE NOT NULL,
                price REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'RUB',
                payment_period TEXT NOT NULL DEFAULT 'monthly',
                notes TEXT,
                tags TEXT,
                is_monitoring BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Миграция: добавляем location если колонка не существует
        cursor = await db.execute("PRAGMA table_info(servers)")
        columns = [row[1] for row in await cursor.fetchall()]
        if 'location' not in columns:
            await db.execute("ALTER TABLE servers ADD COLUMN location TEXT")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                reminder_days INTEGER DEFAULT 7,
                reminder_time TEXT DEFAULT '10:00'
            )
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_servers_user_id ON servers(user_id)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_servers_expiry ON servers(expiry_date)
        """)

        # Таблица API ключей хостингов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                api_key TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, provider)
            )
        """)

        # Добавляем external_id для связи с хостингом
        cursor = await db.execute("PRAGMA table_info(servers)")
        columns = [row[1] for row in await cursor.fetchall()]
        if 'external_id' not in columns:
            await db.execute("ALTER TABLE servers ADD COLUMN external_id TEXT")
        if 'provider' not in columns:
            await db.execute("ALTER TABLE servers ADD COLUMN provider TEXT")

        await db.commit()


class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path

    async def get_server_count(self, user_id: int) -> int:
        """Возвращает количество серверов пользователя."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM servers WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def add_server(
        self,
        user_id: int,
        name: str,
        hosting: str,
        expiry_date: date,
        price: float,
        currency: str = "RUB",
        payment_period: str = "monthly",
        location: Optional[str] = None,
        ip: Optional[str] = None,
        url: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[str] = None
    ) -> int:
        # Проверка лимита серверов
        count = await self.get_server_count(user_id)
        if count >= MAX_SERVERS_PER_USER:
            raise ValueError(f"Превышен лимит серверов ({MAX_SERVERS_PER_USER})")

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO servers (user_id, name, hosting, location, ip, url, expiry_date,
                                     price, currency, payment_period, notes, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, name, hosting, location, ip, url, expiry_date.isoformat(),
                 price, currency, payment_period, notes, tags)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_server(self, server_id: int, user_id: int) -> Optional[Server]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM servers WHERE id = ? AND user_id = ?",
                (server_id, user_id)
            )
            row = await cursor.fetchone()
            if row:
                return self._row_to_server(row)
            return None

    async def get_all_servers(self, user_id: int) -> list[Server]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM servers WHERE user_id = ? ORDER BY expiry_date",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [self._row_to_server(row) for row in rows]

    async def get_expiring_servers(self, user_id: int, days: int = 30) -> list[Server]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM servers
                WHERE user_id = ? AND expiry_date <= date('now', '+' || ? || ' days')
                ORDER BY expiry_date
                """,
                (user_id, days)
            )
            rows = await cursor.fetchall()
            return [self._row_to_server(row) for row in rows]

    async def get_servers_for_reminder(self, days: int) -> list[Server]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM servers
                WHERE expiry_date <= date('now', '+' || ? || ' days')
                  AND expiry_date >= date('now')
                ORDER BY user_id, expiry_date
                """,
                (days,)
            )
            rows = await cursor.fetchall()
            return [self._row_to_server(row) for row in rows]

    async def get_servers_for_monitoring(self) -> list[Server]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM servers
                WHERE is_monitoring = 1 AND (ip IS NOT NULL OR url IS NOT NULL)
                """
            )
            rows = await cursor.fetchall()
            return [self._row_to_server(row) for row in rows]

    async def update_server(self, server_id: int, user_id: int, **kwargs) -> bool:
        if not kwargs:
            return False

        allowed_fields = {
            'name', 'hosting', 'location', 'ip', 'url', 'expiry_date', 'price',
            'currency', 'payment_period', 'notes', 'tags', 'is_monitoring'
        }

        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False

        if 'expiry_date' in updates and isinstance(updates['expiry_date'], date):
            updates['expiry_date'] = updates['expiry_date'].isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [server_id, user_id]

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                f"UPDATE servers SET {set_clause} WHERE id = ? AND user_id = ?",
                values
            )
            await db.commit()
            return cursor.rowcount > 0

    async def delete_server(self, server_id: int, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM servers WHERE id = ? AND user_id = ?",
                (server_id, user_id)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def mark_paid(self, server_id: int, user_id: int) -> Optional[date]:
        server = await self.get_server(server_id, user_id)
        if not server:
            return None

        from dateutil.relativedelta import relativedelta

        period = server.payment_period
        if period == "monthly":
            new_date = server.expiry_date + relativedelta(months=1)
        elif period == "quarterly":
            new_date = server.expiry_date + relativedelta(months=3)
        elif period == "halfyear":
            new_date = server.expiry_date + relativedelta(months=6)
        elif period == "yearly":
            new_date = server.expiry_date + relativedelta(years=1)
        elif period.startswith("custom_"):
            # Формат: custom_N где N - количество месяцев
            try:
                months = int(period.split("_")[1])
                new_date = server.expiry_date + relativedelta(months=months)
            except (IndexError, ValueError):
                new_date = server.expiry_date + relativedelta(months=1)
        else:
            new_date = server.expiry_date + relativedelta(months=1)

        await self.update_server(server_id, user_id, expiry_date=new_date)
        return new_date

    async def get_settings(self, user_id: int) -> UserSettings:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM settings WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            if row:
                return UserSettings(
                    user_id=row['user_id'],
                    reminder_days=row['reminder_days'],
                    reminder_time=row['reminder_time']
                )
            return UserSettings(user_id=user_id, reminder_days=7, reminder_time="10:00")

    async def update_settings(self, user_id: int, **kwargs) -> bool:
        allowed_fields = {'reminder_days', 'reminder_time'}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM settings WHERE user_id = ?",
                (user_id,)
            )
            exists = await cursor.fetchone()

            if exists:
                set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
                values = list(updates.values()) + [user_id]
                await db.execute(
                    f"UPDATE settings SET {set_clause} WHERE user_id = ?",
                    values
                )
            else:
                columns = ['user_id'] + list(updates.keys())
                placeholders = ", ".join("?" for _ in columns)
                values = [user_id] + list(updates.values())
                await db.execute(
                    f"INSERT INTO settings ({', '.join(columns)}) VALUES ({placeholders})",
                    values
                )

            await db.commit()
            return True

    async def get_all_users_with_settings(self) -> list[UserSettings]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT DISTINCT s.user_id,
                       COALESCE(st.reminder_days, 7) as reminder_days,
                       COALESCE(st.reminder_time, '10:00') as reminder_time
                FROM servers s
                LEFT JOIN settings st ON s.user_id = st.user_id
                """
            )
            rows = await cursor.fetchall()
            return [
                UserSettings(
                    user_id=row['user_id'],
                    reminder_days=row['reminder_days'],
                    reminder_time=row['reminder_time']
                )
                for row in rows
            ]

    async def get_unique_hostings(self, user_id: int) -> list[str]:
        """Возвращает уникальные хостинги пользователя."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT DISTINCT hosting FROM servers WHERE user_id = ? ORDER BY hosting",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows if row[0]]

    async def get_unique_locations(self, user_id: int) -> list[str]:
        """Возвращает уникальные локации пользователя."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT DISTINCT location FROM servers WHERE user_id = ? AND location IS NOT NULL ORDER BY location",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows if row[0]]

    async def get_unique_prices(self, user_id: int) -> list[tuple[float, str]]:
        """Возвращает уникальные цены пользователя (price, currency)."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT DISTINCT price, currency FROM servers WHERE user_id = ? ORDER BY currency, price",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [(row[0], row[1]) for row in rows]

    # === API Keys ===

    async def save_api_key(self, user_id: int, provider: str, api_key: str) -> bool:
        """Сохранить или обновить API ключ (с шифрованием)."""
        encrypted_key = encrypt_api_key(api_key)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO api_keys (user_id, provider, api_key)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, provider) DO UPDATE SET
                    api_key = excluded.api_key,
                    created_at = CURRENT_TIMESTAMP
                """,
                (user_id, provider.lower(), encrypted_key)
            )
            await db.commit()
            return True

    async def get_api_key(self, user_id: int, provider: str) -> Optional[str]:
        """Получить API ключ пользователя (с расшифровкой)."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT api_key FROM api_keys WHERE user_id = ? AND provider = ?",
                (user_id, provider.lower())
            )
            row = await cursor.fetchone()
            if row:
                return decrypt_api_key(row[0])
            return None

    async def get_user_api_keys(self, user_id: int) -> list[HostingAPIKey]:
        """Получить все API ключи пользователя."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM api_keys WHERE user_id = ?",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [
                HostingAPIKey(
                    id=row['id'],
                    user_id=row['user_id'],
                    provider=row['provider'],
                    api_key=row['api_key'],
                    created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at']
                )
                for row in rows
            ]

    async def delete_api_key(self, user_id: int, provider: str) -> bool:
        """Удалить API ключ."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM api_keys WHERE user_id = ? AND provider = ?",
                (user_id, provider.lower())
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_server_by_external_id(self, user_id: int, provider: str, external_id: str) -> Optional[Server]:
        """Найти сервер по external_id от хостинга."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM servers WHERE user_id = ? AND provider = ? AND external_id = ?",
                (user_id, provider.lower(), external_id)
            )
            row = await cursor.fetchone()
            if row:
                return self._row_to_server(row)
            return None

    async def add_or_update_server_from_hosting(
        self,
        user_id: int,
        provider: str,
        external_id: str,
        name: str,
        expiry_date: date,
        price: float,
        currency: str = "RUB",
        ip: Optional[str] = None,
        location: Optional[str] = None
    ) -> int:
        """Добавить или обновить сервер из хостинга."""
        existing = await self.get_server_by_external_id(user_id, provider, external_id)

        if existing:
            # Обновляем существующий
            await self.update_server(
                existing.id,
                user_id,
                name=name,
                expiry_date=expiry_date,
                price=price,
                currency=currency,
                ip=ip,
                location=location
            )
            return existing.id
        else:
            # Создаём новый
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    INSERT INTO servers (user_id, name, hosting, location, ip, expiry_date,
                                         price, currency, payment_period, provider, external_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, name, provider.upper(), location, ip, expiry_date.isoformat(),
                     price, currency, "monthly", provider.lower(), external_id)
                )
                await db.commit()
                return cursor.lastrowid

    def _row_to_server(self, row) -> Server:
        expiry = row['expiry_date']
        if isinstance(expiry, str):
            expiry = date.fromisoformat(expiry)

        created = row['created_at']
        if isinstance(created, str):
            created = datetime.fromisoformat(created)

        return Server(
            id=row['id'],
            user_id=row['user_id'],
            name=row['name'],
            hosting=row['hosting'],
            location=row['location'],
            ip=row['ip'],
            url=row['url'],
            expiry_date=expiry,
            price=row['price'],
            currency=row['currency'],
            payment_period=row['payment_period'],
            notes=row['notes'],
            tags=row['tags'],
            is_monitoring=bool(row['is_monitoring']),
            created_at=created
        )


db = Database()
