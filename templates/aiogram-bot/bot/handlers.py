from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.config import Config
from bot.db import Database
from bot.services import texts


def create_router() -> Router:
    """Фабрика: aiogram не даёт подключить один Router к двум диспетчерам,
    а в тестах диспетчер собирается заново на каждый тест."""
    router = Router(name="main")

    @router.message(CommandStart())
    async def cmd_start(message: Message, db: Database) -> None:
        is_new = await db.upsert_user(message.from_user.id, message.from_user.username)
        await message.answer(texts.welcome(message.from_user.first_name, is_new))

    @router.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        await message.answer(texts.HELP)

    @router.message(Command("stats"))
    async def cmd_stats(message: Message, db: Database, config: Config) -> None:
        if not config.is_admin(message.from_user.id):
            await message.answer(texts.NO_ACCESS)
            return
        await message.answer(texts.stats(await db.count_users()))

    @router.message(F.text)
    async def fallback(message: Message) -> None:
        await message.answer(texts.UNKNOWN)

    return router
