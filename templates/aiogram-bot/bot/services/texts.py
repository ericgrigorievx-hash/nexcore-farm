HELP = "Команды:\n/start — начать\n/help — помощь"
NO_ACCESS = "Команда только для админов."
UNKNOWN = "Не понял. Напиши /help."


def welcome(name: str | None, is_new: bool) -> str:
    name = name or "друг"
    return f"Привет, {name}! 👋" if is_new else f"С возвращением, {name}!"


def stats(users: int) -> str:
    return f"Пользователей: {users}"
