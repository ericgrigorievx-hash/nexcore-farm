import pytest
from aiogram.methods import AnswerCallbackQuery, SendDocument, SendPhoto

from bot.db import Database
from bot.services import catalog, texts
from bot.testing import callback_data, callback_update, file_update, sent_messages, sent_texts, text_update
from tests.conftest import ADMIN_ID

TUTOR = 100


async def feed(env, update):
    dp, bot, session, _ = env
    session.requests.clear()
    await dp.feed_update(bot, update)
    return session


async def send(env, text, user_id=TUTOR):
    return sent_texts(await feed(env, text_update(text, user_id=user_id)))


async def click(env, data, user_id=TUTOR, username="tester"):
    return await feed(env, callback_update(data, user_id=user_id, username=username))


async def seed(env):
    await send(env, "/seed_sat", user_id=ADMIN_ID)


async def section_id(db: Database, title: str) -> int:
    return next(s["id"] for s in await db.list_sections() if s["title"] == title)


# --- пользователь ---


async def test_start_greets_saves_user_and_shows_menu(env):
    session = await feed(env, text_update("/start"))
    (msg,) = sent_messages(session)
    assert msg.text == texts.welcome("Тест", True)
    assert callback_data(msg.reply_markup) == ["cat", "my"]
    assert await env[3].count_users() == 1


async def test_catalog_empty_before_seed(env):
    assert await send(env, "/catalog") == [texts.CATALOG_EMPTY]


async def test_catalog_lists_sections_with_topic_counts(env):
    await seed(env)
    session = await click(env, "cat")
    (msg,) = sent_messages(session)
    labels = [b.text for row in msg.reply_markup.inline_keyboard for b in row]
    assert labels == [
        "Algebra (5)",
        "Advanced Math (3)",
        "Problem-Solving and Data Analysis (7)",
        "Geometry and Trigonometry (4)",
    ]
    assert any(isinstance(r, AnswerCallbackQuery) for r in session.requests)


async def test_section_shows_its_topics_and_back_button(env):
    await seed(env)
    sid = await section_id(env[3], "Advanced Math")
    (msg,) = sent_messages(await click(env, f"sec:{sid}"))
    assert callback_data(msg.reply_markup) == ["topic:P.A", "topic:P.B", "topic:P.C", "cat"]
    assert "P.C · Нелинейные функции (259)" in [b.text for row in msg.reply_markup.inline_keyboard for b in row]


async def test_unknown_section_is_handled(env):
    await seed(env)
    assert sent_texts(await click(env, "sec:999")) == [texts.CATALOG_EMPTY]
    assert sent_texts(await click(env, "sec:abc")) == [texts.CATALOG_EMPTY]


async def test_topic_card_has_preview_and_request_buttons(env):
    await seed(env)
    (msg,) = sent_messages(await click(env, "topic:H.A"))
    assert "Линейные уравнения с одной переменной" in msg.text
    assert "Заданий в пакете: 100" in msg.text
    sid = await section_id(env[3], "Algebra")
    assert callback_data(msg.reply_markup) == ["prev:H.A", "req:H.A", f"sec:{sid}"]


async def test_preview_missing_says_soon(env):
    await seed(env)
    assert sent_texts(await click(env, "prev:Q.B")) == [texts.NO_PREVIEW]


@pytest.mark.parametrize("kind,method", [("document", SendDocument), ("photo", SendPhoto)])
async def test_admin_uploads_preview_and_user_receives_it(env, kind, method):
    await seed(env)
    session = await feed(env, file_update("/preview Q.B", kind=kind, user_id=ADMIN_ID, file_id="PREV42"))
    assert sent_texts(session) == [texts.preview_saved("Q.B")]
    session = await click(env, "prev:Q.B")
    sent = [r for r in session.requests if isinstance(r, method)]
    assert len(sent) == 1
    assert (sent[0].document if kind == "document" else sent[0].photo) == "PREV42"


async def test_request_creates_record_and_notifies_admin(env):
    await seed(env)
    session = await click(env, "req:S.D")
    msgs = sent_messages(session)
    topic = await env[3].get_topic("S.D")
    assert msgs[0].chat_id == TUTOR and msgs[0].text == texts.request_created(topic)
    admin_msg = msgs[1]
    assert admin_msg.chat_id == ADMIN_ID
    assert "@tester" in admin_msg.text and "S.D" in admin_msg.text
    (req,) = await env[3].list_requests(status="new")
    assert req["user_id"] == TUTOR and req["topic_code"] == "S.D"
    assert callback_data(admin_msg.reply_markup) == [f"adm:done:{req['id']}", f"adm:rejected:{req['id']}"]


async def test_repeat_request_is_not_duplicated(env):
    await seed(env)
    await click(env, "req:S.D")
    session = await click(env, "req:S.D")
    topic = await env[3].get_topic("S.D")
    assert sent_texts(session) == [texts.request_duplicate(topic)]
    assert await env[3].count_requests() == (1, 1)


async def test_request_without_username_links_user_id(env):
    await seed(env)
    session = await click(env, "req:H.B", username=None)
    admin_text = sent_texts(session)[1]
    assert f"tg://user?id={TUTOR}" in admin_text


async def test_hidden_topic_cannot_be_opened_or_requested(env):
    await seed(env)
    assert await send(env, "/hide P.A", user_id=ADMIN_ID) == [texts.topic_visibility("P.A", False)]
    for data in ("topic:P.A", "req:P.A", "prev:P.A"):
        session = await click(env, data)
        assert sent_texts(session) == []
        (ans,) = [r for r in session.requests if isinstance(r, AnswerCallbackQuery)]
        assert ans.text == texts.TOPIC_NOT_FOUND
    assert await env[3].count_requests() == (0, 0)
    # раздел Advanced Math теперь показывает 2 темы
    sections = {s["title"]: s["topics"] for s in await env[3].list_sections()}
    assert sections["Advanced Math"] == 2
    assert await send(env, "/show P.A", user_id=ADMIN_ID) == [texts.topic_visibility("P.A", True)]
    assert sent_messages(await click(env, "topic:P.A"))


async def test_my_requests_shows_statuses(env):
    await seed(env)
    assert await send(env, "/my") == [texts.MY_EMPTY]
    await click(env, "req:H.A")
    await click(env, "req:H.B")
    (req_b, req_a) = await env[3].list_requests(user_id=TUTOR)
    await env[3].close_request(req_a["id"], "done")
    (text,) = await send(env, "/my")
    assert "Линейные функции — 🕓 новая" in text
    assert "Линейные уравнения с одной переменной — ✅ выполнена" in text


# --- админ ---


async def test_admin_commands_denied_for_regular_user(env):
    for cmd in ("/admin", "/stats", "/seed_sat", "/addtopic X | Y | Z | 1", "/hide H.A", "/requests"):
        assert await send(env, cmd, user_id=555) == [texts.NO_ACCESS]
    session = await feed(env, file_update("/preview H.A", user_id=555))
    assert sent_texts(session) == [texts.NO_ACCESS]
    assert await env[3].count_topics() == (0, 0)


async def test_seed_is_idempotent_and_keeps_preview(env):
    assert await send(env, "/seed_sat", user_id=ADMIN_ID) == [texts.seeded(19, 19)]
    await env[3].set_preview("H.A", "KEEP", "document")
    assert await send(env, "/seed_sat", user_id=ADMIN_ID) == [texts.seeded(0, 19)]
    assert (await env[3].get_topic("H.A"))["preview_file_id"] == "KEEP"
    assert await env[3].count_topics() == (19, 19)


async def test_addtopic_creates_and_updates(env):
    r = await send(env, "/addtopic RW.1 | Reading and Writing | Словарь в контексте | 40", user_id=ADMIN_ID)
    assert r == [texts.topic_saved("RW.1", True)]
    r = await send(env, "/addtopic RW.1 | Reading and Writing | Слова в контексте | 45", user_id=ADMIN_ID)
    assert r == [texts.topic_saved("RW.1", False)]
    t = await env[3].get_topic("RW.1")
    assert (t["title"], t["tasks_count"], t["section_title"]) == ("Слова в контексте", 45, "Reading and Writing")


@pytest.mark.parametrize(
    "args",
    ["", "A | B | C", "A | B | C | много", "плохой код | B | C | 1", "A |  | C | 1"],
)
def test_parse_addtopic_rejects_bad_input(args):
    with pytest.raises(catalog.ParseError):
        catalog.parse_addtopic(args)


async def test_addtopic_bad_format_replies_hint(env):
    (reply,) = await send(env, "/addtopic только код", user_id=ADMIN_ID)
    assert "4 поля" in reply


async def test_preview_errors(env):
    await seed(env)
    assert await send(env, "/preview H.A", user_id=ADMIN_ID) == [texts.PREVIEW_USAGE]
    session = await feed(env, file_update("/preview NOPE", user_id=ADMIN_ID))
    assert sent_texts(session) == [texts.topic_unknown("NOPE")]
    assert await send(env, "/hide NOPE", user_id=ADMIN_ID) == [texts.topic_unknown("NOPE")]


async def test_admin_closes_request_and_user_is_notified(env):
    await seed(env)
    await click(env, "req:Q.E")
    (req,) = await env[3].list_requests(status="new")
    msgs = sent_messages(await click(env, f"adm:done:{req['id']}", user_id=ADMIN_ID))
    assert msgs[0].chat_id == ADMIN_ID and msgs[0].text == texts.admin_request_closed(req["id"], "done")
    assert msgs[1].chat_id == TUTOR and "выполнена" in msgs[1].text
    assert (await env[3].get_request(req["id"]))["status"] == "done"
    # повторное нажатие — уже обработана, статус не меняется
    session = await click(env, f"adm:rejected:{req['id']}", user_id=ADMIN_ID)
    (ans,) = [r for r in session.requests if isinstance(r, AnswerCallbackQuery)]
    assert ans.text == texts.REQUEST_ALREADY_CLOSED
    assert (await env[3].get_request(req["id"]))["status"] == "done"


async def test_regular_user_cannot_close_requests(env):
    await seed(env)
    await click(env, "req:Q.E")
    (req,) = await env[3].list_requests(status="new")
    await click(env, f"adm:rejected:{req['id']}", user_id=555)
    assert (await env[3].get_request(req["id"]))["status"] == "new"


async def test_requests_list_and_admin_panel(env):
    await seed(env)
    assert await send(env, "/requests", user_id=ADMIN_ID) == [texts.REQUESTS_EMPTY]
    await click(env, "req:H.A", user_id=10)
    await click(env, "req:H.B", user_id=11)
    msgs = sent_messages(await feed(env, text_update("/requests", user_id=ADMIN_ID)))
    assert len(msgs) == 2 and all(m.reply_markup for m in msgs)
    (panel,) = await send(env, "/admin", user_id=ADMIN_ID)
    assert panel == texts.admin_panel(2, 19, 19, 2, 2)


async def test_unknown_text_fallback(env):
    assert await send(env, "абракадабра") == [texts.UNKNOWN]


def test_sat_seed_matches_workspace_snapshot():
    assert len(catalog.SAT_TOPICS) == 19
    assert len({t.code for t in catalog.SAT_TOPICS}) == 19
    assert sum(t.tasks_count for t in catalog.SAT_TOPICS) == 1913
    assert all(catalog.is_valid_code(t.code) for t in catalog.SAT_TOPICS)
    # callback_data в Telegram ≤ 64 байт
    assert all(len(f"topic:{t.code}".encode()) <= 64 for t in catalog.SAT_TOPICS)
