"""Офлайн-бот для тестов: прогоняет апдейты через настоящий Dispatcher,
но вместо Telegram API складывает исходящие запросы в список."""

import itertools
from datetime import datetime

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods import SendMessage, TelegramMethod
from aiogram.types import Chat, Message, Update, User

_ids = itertools.count(1)


class FakeSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[TelegramMethod] = []

    async def make_request(self, bot, method, timeout=None):
        self.requests.append(method)
        if isinstance(method, SendMessage):
            return Message(
                message_id=next(_ids),
                date=datetime.now(),
                chat=Chat(id=method.chat_id, type="private"),
                text=method.text,
            )
        return True

    async def stream_content(self, *args, **kwargs):
        if False:
            yield b""

    async def close(self) -> None:
        pass


def make_bot() -> tuple[Bot, FakeSession]:
    session = FakeSession()
    bot = Bot("42:FAKE-TOKEN-FOR-TESTS", session=session)
    return bot, session


def text_update(text: str, user_id: int = 100, username: str = "tester", first_name: str = "Тест") -> Update:
    user = User(id=user_id, is_bot=False, first_name=first_name, username=username)
    msg = Message(
        message_id=next(_ids),
        date=datetime.now(),
        chat=Chat(id=user_id, type="private"),
        from_user=user,
        text=text,
    )
    return Update(update_id=next(_ids), message=msg)


def sent_texts(session: FakeSession) -> list[str]:
    return [r.text for r in session.requests if isinstance(r, SendMessage)]
