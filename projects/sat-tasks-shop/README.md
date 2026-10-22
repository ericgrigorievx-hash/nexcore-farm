# SAT Tasks Shop — витрина SAT Math заданий для репетиторов

Telegram-бот: каталог тем SAT Math (4 раздела, 19 тем) → карточка темы → превью → «Запросить пакет».
Заявка падает админам с кнопками «✅ Выполнено / ✖️ Отклонить», репетитор получает уведомление о статусе.
Оплаты нет: пакет админ отправляет сам после договорённости. Темы, превью и видимость админ меняет через бота.

## Команды
Пользователь: `/start`, `/catalog`, `/my` (мои заявки), `/help`.

Админ (ID из `ADMIN_IDS`):
| Команда | Что делает |
|---|---|
| `/admin` (или `/stats`) | метрики + шпаргалка |
| `/seed_sat` | загрузить 19 тем SAT Math (повторно — безопасно, превью не стирает) |
| `/addtopic CODE \| Раздел \| Название \| Кол-во` | создать/обновить тему (например, для Reading & Writing) |
| документ или фото с подписью `/preview CODE` | превью темы (лучше 1–2 страницы, без ответов) |
| `/hide CODE`, `/show CODE` | скрыть/вернуть тему |
| `/requests` | 10 последних новых заявок с кнопками |

## Первый запуск (контент)
1. Админ пишет боту `/start`, затем `/seed_sat`.
2. Для каждой темы присылает превью с подписью `/preview H.A` и т.д. Полные PDF лежат у Эрика
   в `Workspace/SAT/<Раздел>/<Код_Тема>/` — в репозиторий их не кладём.
3. Пакеты (Zadaniya + Otvety PDF) админ отправляет репетитору вручную после заявки.

## Переменные окружения
| Переменная | Зачем |
|---|---|
| `BOT_TOKEN` | токен от @BotFather |
| `ADMIN_IDS` | Telegram ID админов через запятую (им приходят заявки; каждый админ должен нажать /start у бота) |
| `DB_PATH` | путь к SQLite (на Railway — в volume: `/data/bot.db`) |

## Локально
```
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q && python -m scripts.smoke
python -m bot.main
```

## Деплой на Railway
New Service → GitHub repo `nexcore-farm` → Settings → Root Directory = `projects/sat-tasks-shop` →
Start Command берётся из `railway.json` (`python -m bot.main`) →
Variables: `BOT_TOKEN`, `ADMIN_IDS`, `DB_PATH=/data/bot.db` → Volume, смонтированный в `/data`.

## Устройство
- `bot/handlers.py` — пользовательские сценарии, `bot/admin.py` — админка (оба через `create_router()`)
- `bot/db.py` — SQLite: `sections`, `topics`, `requests`, `users`
- `bot/services/catalog.py` — сид тем SAT и разбор админ-команд (чистые функции)
- Спека и что взято у доноров — `SPEC.md`
