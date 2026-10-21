# <Название бота>

Что делает: …

## Команды
- `/start`, `/help`, `/stats` (админ)

## Переменные окружения
| Переменная | Зачем |
|---|---|
| `BOT_TOKEN` | токен от @BotFather |
| `ADMIN_IDS` | Telegram ID админов через запятую |
| `DB_PATH` | путь к SQLite (на Railway — в volume, напр. `/data/bot.db`) |

## Локально
```
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q && python -m scripts.smoke
python -m bot.main
```

## Деплой на Railway
New Service → GitHub repo `nexcore-farm` → Settings → Root Directory = `projects/<slug>` →
Variables: из таблицы выше → (для SQLite) Volume, смонтированный в `/data`.
