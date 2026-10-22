import os

import aiosqlite

from bot.services.catalog import TopicSeed

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE,
    sort INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS topics (
    code TEXT PRIMARY KEY,
    section_id INTEGER NOT NULL REFERENCES sections(id),
    title TEXT NOT NULL,
    tasks_count INTEGER NOT NULL DEFAULT 0,
    preview_file_id TEXT,
    preview_kind TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    sort INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    first_name TEXT,
    topic_code TEXT NOT NULL REFERENCES topics(code),
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    closed_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS ix_requests_user ON requests(user_id);
"""

STATUSES = ("new", "done", "rejected")


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

    # --- users ---
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

    # --- catalog ---
    async def _section_id(self, title: str) -> int:
        cur = await self.conn.execute("SELECT id FROM sections WHERE title = ?", (title,))
        row = await cur.fetchone()
        if row:
            return row["id"]
        cur = await self.conn.execute(
            "INSERT INTO sections (title, sort) VALUES (?, (SELECT COALESCE(MAX(sort), 0) + 1 FROM sections))",
            (title,),
        )
        return cur.lastrowid

    async def upsert_topic(self, seed: TopicSeed) -> bool:
        """Создаёт или обновляет тему (превью и видимость не трогает). True — если создана."""
        section_id = await self._section_id(seed.section)
        cur = await self.conn.execute("SELECT 1 FROM topics WHERE code = ?", (seed.code,))
        exists = await cur.fetchone()
        if exists:
            await self.conn.execute(
                "UPDATE topics SET section_id = ?, title = ?, tasks_count = ? WHERE code = ?",
                (section_id, seed.title, seed.tasks_count, seed.code),
            )
        else:
            await self.conn.execute(
                "INSERT INTO topics (code, section_id, title, tasks_count, sort) "
                "VALUES (?, ?, ?, ?, (SELECT COALESCE(MAX(sort), 0) + 1 FROM topics))",
                (seed.code, section_id, seed.title, seed.tasks_count),
            )
        await self.conn.commit()
        return not exists

    async def get_topic(self, code: str) -> dict | None:
        cur = await self.conn.execute(
            "SELECT t.*, s.title AS section_title FROM topics t JOIN sections s ON s.id = t.section_id "
            "WHERE t.code = ?",
            (code,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def set_topic_active(self, code: str, active: bool) -> bool:
        cur = await self.conn.execute("UPDATE topics SET is_active = ? WHERE code = ?", (int(active), code))
        await self.conn.commit()
        return cur.rowcount > 0

    async def set_preview(self, code: str, file_id: str, kind: str) -> bool:
        cur = await self.conn.execute(
            "UPDATE topics SET preview_file_id = ?, preview_kind = ? WHERE code = ?", (file_id, kind, code)
        )
        await self.conn.commit()
        return cur.rowcount > 0

    async def list_sections(self) -> list[dict]:
        """Разделы, где есть хотя бы одна активная тема."""
        cur = await self.conn.execute(
            "SELECT s.id, s.title, COUNT(t.code) AS topics FROM sections s "
            "JOIN topics t ON t.section_id = s.id AND t.is_active = 1 "
            "GROUP BY s.id ORDER BY s.sort"
        )
        return [dict(r) for r in await cur.fetchall()]

    async def get_section_title(self, section_id: int) -> str | None:
        cur = await self.conn.execute("SELECT title FROM sections WHERE id = ?", (section_id,))
        row = await cur.fetchone()
        return row["title"] if row else None

    async def list_topics(self, section_id: int) -> list[dict]:
        cur = await self.conn.execute(
            "SELECT * FROM topics WHERE section_id = ? AND is_active = 1 ORDER BY sort", (section_id,)
        )
        return [dict(r) for r in await cur.fetchall()]

    async def count_topics(self) -> tuple[int, int]:
        cur = await self.conn.execute("SELECT COALESCE(SUM(is_active), 0), COUNT(*) FROM topics")
        active, total = await cur.fetchone()
        return active, total

    # --- requests ---
    async def find_open_request(self, user_id: int, code: str) -> int | None:
        cur = await self.conn.execute(
            "SELECT id FROM requests WHERE user_id = ? AND topic_code = ? AND status = 'new'", (user_id, code)
        )
        row = await cur.fetchone()
        return row["id"] if row else None

    async def create_request(self, user_id: int, username: str | None, first_name: str | None, code: str) -> int:
        cur = await self.conn.execute(
            "INSERT INTO requests (user_id, username, first_name, topic_code) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, code),
        )
        await self.conn.commit()
        return cur.lastrowid

    async def get_request(self, request_id: int) -> dict | None:
        cur = await self.conn.execute(
            "SELECT r.*, t.title AS topic_title FROM requests r JOIN topics t ON t.code = r.topic_code "
            "WHERE r.id = ?",
            (request_id,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def close_request(self, request_id: int, status: str) -> bool:
        """new → done/rejected. False, если заявки нет или она уже закрыта."""
        if status not in ("done", "rejected"):
            raise ValueError(status)
        cur = await self.conn.execute(
            "UPDATE requests SET status = ?, closed_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'new'",
            (status, request_id),
        )
        await self.conn.commit()
        return cur.rowcount > 0

    async def list_requests(self, *, status: str | None = None, user_id: int | None = None, limit: int = 10) -> list[dict]:
        where, params = [], []
        if status:
            where.append("r.status = ?")
            params.append(status)
        if user_id is not None:
            where.append("r.user_id = ?")
            params.append(user_id)
        sql = (
            "SELECT r.*, t.title AS topic_title FROM requests r JOIN topics t ON t.code = r.topic_code"
            + (" WHERE " + " AND ".join(where) if where else "")
            + " ORDER BY r.id DESC LIMIT ?"
        )
        cur = await self.conn.execute(sql, (*params, limit))
        return [dict(r) for r in await cur.fetchall()]

    async def count_requests(self) -> tuple[int, int]:
        cur = await self.conn.execute("SELECT COALESCE(SUM(status = 'new'), 0), COUNT(*) FROM requests")
        new, total = await cur.fetchone()
        return new, total
