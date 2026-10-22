import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _ids(raw: str) -> list[int]:
    return [int(x) for x in raw.replace(" ", "").split(",") if x]


@dataclass(frozen=True)
class Config:
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "data/bot.db"))
    admin_ids: list[int] = field(default_factory=lambda: _ids(os.getenv("ADMIN_IDS", "")))

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids
