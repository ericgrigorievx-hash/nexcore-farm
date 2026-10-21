"""Smoke: бот собирается, роутеры подключены, /start отвечает. Без сети и без токена.
Запуск: python -m scripts.smoke"""

import asyncio
import sys

from bot.config import Config
from bot.db import Database
from bot.main import build_dispatcher
from bot.testing import make_bot, sent_texts, text_update


async def main() -> int:
    db = Database(":memory:")
    await db.connect()
    dp = build_dispatcher(db, Config(bot_token="smoke", db_path=":memory:", admin_ids=[]))
    bot, session = make_bot()

    routers = list(dp.chain_tail)
    handlers = sum(len(r.message.handlers) + len(r.callback_query.handlers) for r in routers)
    await dp.feed_update(bot, text_update("/start"))
    replies = sent_texts(session)
    await db.close()

    ok = handlers > 0 and len(replies) > 0
    print(f"routers={len(routers)} handlers={handlers} start_replies={len(replies)} -> {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
