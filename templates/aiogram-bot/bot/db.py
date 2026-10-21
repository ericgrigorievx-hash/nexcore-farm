import os

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        if self.path != ":memory:":
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.executescript(SCHEMA)
        await self.conn.commit()

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()

    async def upsert_user(self, user_id: int, username: str | None) -> bool:
        """Возвращает True, если пользователь новый."""
        cur = await self.conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
        exists = await cur.fetchone()
        if exists:
            await self.conn.execute("UPDATE users SET username = ? WHERE id = ?", (username, user_id))
        else:
            await self.conn.execute("INSERT INTO users (id, username) VALUES (?, ?)", (user_id, username))
        await self.conn.commit()
        return not exists

    async def count_users(self) -> int:
        cur = await self.conn.execute("SELECT COUNT(*) FROM users")
        (n,) = await cur.fetchone()
        return n
