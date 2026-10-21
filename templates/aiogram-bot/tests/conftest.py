import pytest_asyncio

from bot.config import Config
from bot.db import Database
from bot.main import build_dispatcher
from bot.testing import make_bot

ADMIN_ID = 1


@pytest_asyncio.fixture
async def db():
    database = Database(":memory:")
    await database.connect()
    yield database
    await database.close()


@pytest_asyncio.fixture
async def env(db):
    """(dp, bot, session, db) — полный офлайн-стенд бота."""
    config = Config(bot_token="test", db_path=":memory:", admin_ids=[ADMIN_ID])
    dp = build_dispatcher(db, config)
    bot, session = make_bot()
    yield dp, bot, session, db
