"""Админка прямо в боте (по мотивам handlers/admin.py из OGE Math Bot): темы, превью, заявки."""

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from bot import keyboards
from bot.config import Config
from bot.db import Database
from bot.services import catalog, texts

log = logging.getLogger(__name__)


def create_router() -> Router:
    router = Router(name="admin")

    async def guard(message: Message, config: Config) -> bool:
        if config.is_admin(message.from_user.id):
            return True
        await message.answer(texts.NO_ACCESS)
        return False

    @router.message(Command("admin", "stats"))
    async def cmd_admin(message: Message, db: Database, config: Config) -> None:
        if not await guard(message, config):
            return
        await message.answer(
            texts.admin_panel(await db.count_users(), *await db.count_topics(), *await db.count_requests())
        )

    @router.message(Command("seed_sat"))
    async def cmd_seed(message: Message, db: Database, config: Config) -> None:
        if not await guard(message, config):
            return
        created = 0
        for seed in catalog.SAT_TOPICS:
            created += await db.upsert_topic(seed)
        await message.answer(texts.seeded(created, len(catalog.SAT_TOPICS)))

    @router.message(Command("addtopic"))
    async def cmd_addtopic(message: Message, command: CommandObject, db: Database, config: Config) -> None:
        if not await guard(message, config):
            return
        try:
            seed = catalog.parse_addtopic(command.args)
        except catalog.ParseError as exc:
            await message.answer(str(exc))
            return
        await message.answer(texts.topic_saved(seed.code, await db.upsert_topic(seed)))

    async def toggle(message: Message, command: CommandObject, db: Database, config: Config, active: bool) -> None:
        if not await guard(message, config):
            return
        try:
            code = catalog.parse_code(command.args)
        except catalog.ParseError as exc:
            await message.answer(str(exc))
            return
        if await db.set_topic_active(code, active):
            await message.answer(texts.topic_visibility(code, active))
        else:
            await message.answer(texts.topic_unknown(code))

    @router.message(Command("hide"))
    async def cmd_hide(message: Message, command: CommandObject, db: Database, config: Config) -> None:
        await toggle(message, command, db, config, False)

    @router.message(Command("show"))
    async def cmd_show(message: Message, command: CommandObject, db: Database, config: Config) -> None:
        await toggle(message, command, db, config, True)

    @router.message(Command("preview"))
    async def cmd_preview(message: Message, command: CommandObject, db: Database, config: Config) -> None:
        if not await guard(message, config):
            return
        if message.document:
            file_id, kind = message.document.file_id, "document"
        elif message.photo:
            file_id, kind = message.photo[-1].file_id, "photo"
        else:
            await message.answer(texts.PREVIEW_USAGE)
            return
        try:
            code = catalog.parse_code(command.args)
        except catalog.ParseError as exc:
            await message.answer(str(exc))
            return
        if await db.set_preview(code, file_id, kind):
            await message.answer(texts.preview_saved(code))
        else:
            await message.answer(texts.topic_unknown(code))

    @router.message(Command("requests"))
    async def cmd_requests(message: Message, db: Database, config: Config) -> None:
        if not await guard(message, config):
            return
        rows = await db.list_requests(status="new", limit=10)
        if not rows:
            await message.answer(texts.REQUESTS_EMPTY)
            return
        for r in rows:
            await message.answer(texts.admin_request_line(r), reply_markup=keyboards.request_actions(r["id"]))

    @router.callback_query(F.data.startswith("adm:"))
    async def cb_close(cb: CallbackQuery, db: Database, config: Config, bot: Bot) -> None:
        if not config.is_admin(cb.from_user.id):
            await cb.answer(texts.NO_ACCESS, show_alert=True)
            return
        _, status, raw_id = cb.data.split(":", 2)
        if status not in ("done", "rejected") or not raw_id.isdigit():
            await cb.answer()
            return
        request_id = int(raw_id)
        if not await db.close_request(request_id, status):
            await cb.answer(texts.REQUEST_ALREADY_CLOSED, show_alert=True)
            return
        await cb.answer()
        await cb.message.answer(texts.admin_request_closed(request_id, status))
        request = await db.get_request(request_id)
        try:
            await bot.send_message(request["user_id"], texts.user_request_closed(request, status))
        except TelegramAPIError as exc:
            log.warning("Не удалось уведомить пользователя %s: %s", request["user_id"], exc)

    return router
