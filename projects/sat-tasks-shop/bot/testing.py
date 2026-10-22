"""Офлайн-бот для тестов: прогоняет апдейты через настоящий Dispatcher,
но вместо Telegram API складывает исходящие запросы в список."""

import itertools
from datetime import datetime

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods import SendDocument, SendMessage, SendPhoto, TelegramMethod
from aiogram.types import CallbackQuery, Chat, Document, Message, PhotoSize, Update, User

_ids = itertools.count(1)


class FakeSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[TelegramMethod] = []

    async def make_request(self, bot, method, timeout=None):
        self.requests.append(method)
        if isinstance(method, (SendMessage, SendDocument, SendPhoto)):
            return Message(
                message_id=next(_ids),
                date=datetime.now(),
                chat=Chat(id=method.chat_id, type="private"),
                text=getattr(method, "text", None),
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


def _user(user_id: int, username: str | None, first_name: str) -> User:
    return User(id=user_id, is_bot=False, first_name=first_name, username=username)


def text_update(text: str, user_id: int = 100, username: str = "tester", first_name: str = "Тест") -> Update:
    msg = Message(
        message_id=next(_ids),
        date=datetime.now(),
        chat=Chat(id=user_id, type="private"),
        from_user=_user(user_id, username, first_name),
        text=text,
    )
    return Update(update_id=next(_ids), message=msg)


def file_update(caption: str, kind: str = "document", user_id: int = 100, file_id: str = "FILE1") -> Update:
    """Сообщение с документом или фото и подписью."""
    extra = (
        {"document": Document(file_id=file_id, file_unique_id=file_id + "u", file_name="preview.pdf")}
        if kind == "document"
        else {"photo": [PhotoSize(file_id=file_id, file_unique_id=file_id + "u", width=100, height=100)]}
    )
    msg = Message(
        message_id=next(_ids),
        date=datetime.now(),
        chat=Chat(id=user_id, type="private"),
        from_user=_user(user_id, "tester", "Тест"),
        caption=caption,
        **extra,
    )
    return Update(update_id=next(_ids), message=msg)


def callback_update(data: str, user_id: int = 100, username: str | None = "tester", first_name: str = "Тест") -> Update:
    user = _user(user_id, username, first_name)
    msg = Message(
        message_id=next(_ids),
        date=datetime.now(),
        chat=Chat(id=user_id, type="private"),
        from_user=User(id=42, is_bot=True, first_name="bot"),
        text="menu",
    )
    cb = CallbackQuery(id=str(next(_ids)), from_user=user, chat_instance="ci", message=msg, data=data)
    return Update(update_id=next(_ids), callback_query=cb)


def sent_texts(session: FakeSession) -> list[str]:
    return [r.text for r in session.requests if isinstance(r, SendMessage)]


def sent_messages(session: FakeSession) -> list[SendMessage]:
    return [r for r in session.requests if isinstance(r, SendMessage)]


def callback_data(markup) -> list[str]:
    """Все callback_data из inline-клавиатуры."""
    return [b.callback_data for row in markup.inline_keyboard for b in row]
