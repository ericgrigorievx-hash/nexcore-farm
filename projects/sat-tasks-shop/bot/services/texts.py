from html import escape

HELP = (
    "Это витрина заданий SAT Math по темам для репетиторов.\n\n"
    "/catalog — каталог тем\n"
    "/my — мои заявки\n"
    "/help — помощь\n\n"
    "Открой тему, посмотри превью и нажми «Запросить пакет» — админ свяжется с тобой."
)
NO_ACCESS = "Команда только для админов."
UNKNOWN = "Не понял. Открой /catalog или напиши /help."
CATALOG_EMPTY = "Каталог пока пуст — темы скоро появятся."
CATALOG_TITLE = "📚 Разделы SAT Math — выбери раздел:"
TOPIC_NOT_FOUND = "Тема не найдена или временно скрыта."
NO_PREVIEW = "Превью для этой темы ещё не загружено — можно сразу запросить пакет."
MY_EMPTY = "Заявок пока нет. Открой /catalog и выбери тему."
REQUESTS_EMPTY = "Новых заявок нет."
REQUEST_ALREADY_CLOSED = "Заявка уже обработана."
PREVIEW_USAGE = "Пришли документ или фото с подписью: /preview CODE"

STATUS_LABEL = {"new": "🕓 новая", "done": "✅ выполнена", "rejected": "✖️ отклонена"}

ADMIN_HELP = (
    "Команды админа:\n"
    "/seed_sat — загрузить 19 тем SAT Math\n"
    "/addtopic CODE | Раздел | Название | Кол-во — тема\n"
    "документ/фото с подписью /preview CODE — превью\n"
    "/hide CODE, /show CODE — скрыть/вернуть тему\n"
    "/requests — новые заявки"
)


def welcome(name: str | None, is_new: bool) -> str:
    name = escape(name or "друг")
    head = f"Привет, {name}! 👋" if is_new else f"С возвращением, {name}!"
    return f"{head}\nЗдесь задания SAT Math, разложенные по темам. Выбирай тему и запрашивай пакет."


def stats(users: int) -> str:
    return f"Пользователей: {users}"


def admin_panel(users: int, topics_active: int, topics_total: int, req_new: int, req_total: int) -> str:
    return (
        "Администратор\n\n"
        f"Пользователей: {users}\n"
        f"Тем: {topics_active} активных из {topics_total}\n"
        f"Заявок: {req_new} новых, всего {req_total}\n\n" + ADMIN_HELP
    )


def section_title(title: str) -> str:
    return f"📂 {escape(title)} — выбери тему:"


def topic_button(t: dict) -> str:
    return f"{t['code']} · {t['title']} ({t['tasks_count']})"


def topic_card(t: dict) -> str:
    return (
        f"<b>{escape(t['code'])} · {escape(t['title'])}</b>\n"
        f"Раздел: {escape(t['section_title'])}\n"
        f"Заданий в пакете: {t['tasks_count']}\n"
        "В пакете: PDF с заданиями по возрастанию сложности + PDF с ответами и разборами."
    )


def preview_caption(t: dict) -> str:
    return f"Превью: {t['code']} · {t['title']}"


def request_created(t: dict) -> str:
    return f"📨 Заявка на «{escape(t['title'])}» отправлена. Админ свяжется с тобой в Telegram."


def request_duplicate(t: dict) -> str:
    return f"Заявка на «{escape(t['title'])}» уже в работе — админ скоро ответит."


def _who(r: dict) -> str:
    if r.get("username"):
        return "@" + escape(r["username"])
    return f'<a href="tg://user?id={r["user_id"]}">{escape(r.get("first_name") or "пользователь")}</a>'


def admin_new_request(r: dict) -> str:
    return f"🆕 Заявка #{r['id']}: {_who(r)} — {escape(r['topic_code'])} · {escape(r['topic_title'])}"


def admin_request_line(r: dict) -> str:
    return f"#{r['id']} {_who(r)} — {escape(r['topic_code'])} · {escape(r['topic_title'])} ({r['created_at']})"


def my_requests(rows: list[dict]) -> str:
    lines = ["📨 Мои заявки:"]
    for r in rows:
        lines.append(f"#{r['id']} {escape(r['topic_title'])} — {STATUS_LABEL.get(r['status'], r['status'])}")
    return "\n".join(lines)


def user_request_closed(r: dict, status: str) -> str:
    if status == "done":
        return f"✅ Заявка #{r['id']} на «{escape(r['topic_title'])}» выполнена. Спасибо!"
    return f"Заявка #{r['id']} на «{escape(r['topic_title'])}» отклонена. Вопросы — напиши админу."


def admin_request_closed(request_id: int, status: str) -> str:
    return f"Заявка #{request_id}: {STATUS_LABEL[status]}"


def seeded(created: int, total: int) -> str:
    return f"Темы SAT загружены: новых {created}, всего в сиде {total}."


def topic_saved(code: str, created: bool) -> str:
    return f"Тема {code} {'создана' if created else 'обновлена'}."


def topic_visibility(code: str, active: bool) -> str:
    return f"Тема {code} {'снова видна' if active else 'скрыта'}."


def topic_unknown(code: str) -> str:
    return f"Темы {escape(code)} нет. Создай её через /addtopic."


def preview_saved(code: str) -> str:
    return f"Превью для {code} сохранено."
