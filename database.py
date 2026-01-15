import aiosqlite
from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass

from config import DATABASE_PATH


@dataclass
class Server:
    id: int
    user_id: int
    name: str
    hosting: str
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


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                hosting TEXT NOT NULL,
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

        await db.commit()


class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path

    async def add_server(
        self,
        user_id: int,
        name: str,
        hosting: str,
        expiry_date: date,
        price: float,
        currency: str = "RUB",
        payment_period: str = "monthly",
        ip: Optional[str] = None,
        url: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[str] = None
    ) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO servers (user_id, name, hosting, ip, url, expiry_date,
                                     price, currency, payment_period, notes, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, name, hosting, ip, url, expiry_date.isoformat(),
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
            'name', 'hosting', 'ip', 'url', 'expiry_date', 'price',
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

        if server.payment_period == "monthly":
            from dateutil.relativedelta import relativedelta
            new_date = server.expiry_date + relativedelta(months=1)
        elif server.payment_period == "yearly":
            from dateutil.relativedelta import relativedelta
            new_date = server.expiry_date + relativedelta(years=1)
        else:
            from datetime import timedelta
            new_date = server.expiry_date + timedelta(days=30)

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
