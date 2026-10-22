from aiogram.types import InlineKeyboardButton as B
from aiogram.types import InlineKeyboardMarkup

from bot.services import texts


def _kb(rows: list[list[B]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_menu() -> InlineKeyboardMarkup:
    return _kb([[B(text="📚 Каталог тем", callback_data="cat")], [B(text="📨 Мои заявки", callback_data="my")]])


def sections(rows: list[dict]) -> InlineKeyboardMarkup:
    return _kb([[B(text=f"{s['title']} ({s['topics']})", callback_data=f"sec:{s['id']}")] for s in rows])


def topics(rows: list[dict]) -> InlineKeyboardMarkup:
    kb = [[B(text=texts.topic_button(t), callback_data=f"topic:{t['code']}")] for t in rows]
    kb.append([B(text="⬅️ К разделам", callback_data="cat")])
    return _kb(kb)


def topic_card(code: str, section_id: int) -> InlineKeyboardMarkup:
    return _kb(
        [
            [B(text="👀 Превью", callback_data=f"prev:{code}")],
            [B(text="📨 Запросить пакет", callback_data=f"req:{code}")],
            [B(text="⬅️ К темам", callback_data=f"sec:{section_id}")],
        ]
    )


def request_actions(request_id: int) -> InlineKeyboardMarkup:
    return _kb(
        [
            [
                B(text="✅ Выполнено", callback_data=f"adm:done:{request_id}"),
                B(text="✖️ Отклонить", callback_data=f"adm:rejected:{request_id}"),
            ]
        ]
    )
