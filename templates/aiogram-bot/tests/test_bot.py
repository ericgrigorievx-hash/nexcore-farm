import pytest

from bot.services import texts
from bot.testing import sent_texts, text_update
from tests.conftest import ADMIN_ID


async def send(env, text, user_id=100):
    dp, bot, session, _ = env
    session.requests.clear()
    await dp.feed_update(bot, text_update(text, user_id=user_id))
    return sent_texts(session)


async def test_start_new_user_greeted_and_saved(env):
    replies = await send(env, "/start")
    assert replies == [texts.welcome("Тест", True)]
    assert await env[3].count_users() == 1


async def test_start_twice_says_welcome_back(env):
    await send(env, "/start")
    replies = await send(env, "/start")
    assert replies == [texts.welcome("Тест", False)]
    assert await env[3].count_users() == 1


async def test_help(env):
    assert await send(env, "/help") == [texts.HELP]


async def test_stats_denied_for_regular_user(env):
    assert await send(env, "/stats", user_id=555) == [texts.NO_ACCESS]


async def test_stats_for_admin(env):
    await send(env, "/start", user_id=10)
    await send(env, "/start", user_id=11)
    assert await send(env, "/stats", user_id=ADMIN_ID) == [texts.stats(2)]


async def test_unknown_text_fallback(env):
    assert await send(env, "абракадабра") == [texts.UNKNOWN]


@pytest.mark.parametrize("name,expected", [(None, "друг"), ("Эрик", "Эрик")])
def test_welcome_name(name, expected):
    assert expected in texts.welcome(name, True)
