import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import Config
from bot.db import Database
from bot.admin import create_router as create_admin_router
from bot.handlers import create_router as create_main_router


def build_dispatcher(db: Database, config: Config) -> Dispatcher:
    """Собирает диспетчер без сети — используется в боте, тестах и smoke."""
    dp = Dispatcher()
    dp["db"] = db
    dp["config"] = config
    # Новые роутеры: создавать фабрикой create_router() и подключать здесь; main (с fallback) — последним.
    dp.include_router(create_admin_router())
    dp.include_router(create_main_router())
    return dp


async def run() -> None:
    logging.basicConfig(level=logging.INFO)
    config = Config()
    if not config.bot_token:
        raise SystemExit("BOT_TOKEN не задан")
    db = Database(config.db_path)
    await db.connect()
    bot = Bot(config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = build_dispatcher(db, config)
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(run())
