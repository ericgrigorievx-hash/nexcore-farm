"""Пользовательские сценарии: каталог → тема → превью → заявка."""

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from bot import keyboards
from bot.config import Config
from bot.db import Database
from bot.services import texts

log = logging.getLogger(__name__)


async def notify_admins(bot: Bot, config: Config, text: str, **kwargs) -> None:
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, text, **kwargs)
        except TelegramAPIError as exc:  # админ мог не нажать /start у бота
            log.warning("Не удалось уведомить админа %s: %s", admin_id, exc)


def create_router() -> Router:
    """Фабрика: aiogram не даёт подключить один Router к двум диспетчерам,
    а в тестах диспетчер собирается заново на каждый тест."""
    router = Router(name="main")

    async def show_catalog(message: Message, db: Database) -> None:
        sections = await db.list_sections()
        if not sections:
            await message.answer(texts.CATALOG_EMPTY)
            return
        await message.answer(texts.CATALOG_TITLE, reply_markup=keyboards.sections(sections))

    async def show_my(message: Message, db: Database, user_id: int) -> None:
        rows = await db.list_requests(user_id=user_id, limit=20)
        await message.answer(texts.my_requests(rows) if rows else texts.MY_EMPTY)

    @router.message(CommandStart())
    async def cmd_start(message: Message, db: Database) -> None:
        is_new = await db.upsert_user(message.from_user.id, message.from_user.username)
        await message.answer(texts.welcome(message.from_user.first_name, is_new), reply_markup=keyboards.main_menu())

    @router.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        await message.answer(texts.HELP)

    @router.message(Command("catalog"))
    async def cmd_catalog(message: Message, db: Database) -> None:
        await show_catalog(message, db)

    @router.message(Command("my"))
    async def cmd_my(message: Message, db: Database) -> None:
        await show_my(message, db, message.from_user.id)

    @router.callback_query(F.data == "cat")
    async def cb_catalog(cb: CallbackQuery, db: Database) -> None:
        await cb.answer()
        await show_catalog(cb.message, db)

    @router.callback_query(F.data == "my")
    async def cb_my(cb: CallbackQuery, db: Database) -> None:
        await cb.answer()
        await show_my(cb.message, db, cb.from_user.id)

    @router.callback_query(F.data.startswith("sec:"))
    async def cb_section(cb: CallbackQuery, db: Database) -> None:
        await cb.answer()
        raw = cb.data.split(":", 1)[1]
        section_id = int(raw) if raw.isdigit() else -1
        title = await db.get_section_title(section_id)
        topics = await db.list_topics(section_id) if title else []
        if not topics:
            await cb.message.answer(texts.CATALOG_EMPTY)
            return
        await cb.message.answer(texts.section_title(title), reply_markup=keyboards.topics(topics))

    async def active_topic(cb: CallbackQuery, db: Database) -> dict | None:
        topic = await db.get_topic(cb.data.split(":", 1)[1])
        if not topic or not topic["is_active"]:
            await cb.answer(texts.TOPIC_NOT_FOUND, show_alert=True)
            return None
        await cb.answer()
        return topic

    @router.callback_query(F.data.startswith("topic:"))
    async def cb_topic(cb: CallbackQuery, db: Database) -> None:
        if topic := await active_topic(cb, db):
            await cb.message.answer(
                texts.topic_card(topic), reply_markup=keyboards.topic_card(topic["code"], topic["section_id"])
            )

    @router.callback_query(F.data.startswith("prev:"))
    async def cb_preview(cb: CallbackQuery, db: Database) -> None:
        topic = await active_topic(cb, db)
        if not topic:
            return
        caption = texts.preview_caption(topic)
        if topic["preview_kind"] == "photo":
            await cb.message.answer_photo(topic["preview_file_id"], caption=caption)
        elif topic["preview_kind"] == "document":
            await cb.message.answer_document(topic["preview_file_id"], caption=caption)
        else:
            await cb.message.answer(texts.NO_PREVIEW)

    @router.callback_query(F.data.startswith("req:"))
    async def cb_request(cb: CallbackQuery, db: Database, config: Config, bot: Bot) -> None:
        topic = await active_topic(cb, db)
        if not topic:
            return
        user = cb.from_user
        if await db.find_open_request(user.id, topic["code"]):
            await cb.message.answer(texts.request_duplicate(topic))
            return
        await db.upsert_user(user.id, user.username)
        request_id = await db.create_request(user.id, user.username, user.first_name, topic["code"])
        await cb.message.answer(texts.request_created(topic))
        request = await db.get_request(request_id)
        await notify_admins(
            bot, config, texts.admin_new_request(request), reply_markup=keyboards.request_actions(request_id)
        )

    @router.message(F.text)
    async def fallback(message: Message) -> None:
        await message.answer(texts.UNKNOWN)

    return router
