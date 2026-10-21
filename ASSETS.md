# Что уже есть у Эрика (снимок C:\Users\Eric\Workspace, 2026-10-22)

Каталог для разведки: перед каждой задачей сначала ищи здесь и на компе, что можно взять готовым.
Снимок может устареть — живая папка на компе главнее. Обновляй этот файл, если нашёл новое.

## Готовый контент
| Что | Где | Заметки |
|---|---|---|
| SAT Math по темам (19 тем, 4 раздела) | `Workspace/SAT/<Раздел>/<Код_Тема>/` | В каждой теме `Zadaniya_1-N.pdf` + `Otvety_i_razbory.pdf`. Разделы: Algebra (H.A–H.E), Advanced_Math (P.A–P.C), Problem-Solving_and_Data_Analysis (Q.A–Q.G), Geometry_and_Trigonometry (S.A–S.D). Архив — `Workspace/SAT.zip` |
| ОГЭ математика, 4300 заданий с ответами | `Workspace/Projects/Flow School/ОГЭ-все-задания-и-ответы-4300.xlsx` | |
| Банк ФИПИ | `Workspace/fipi/`, парсер `Workspace/Claude outputs/fipi_parser_fixed.py` | |
| IELTS-материалы | `Workspace/IELTS/` | |
| Промо-видео и баннеры FACEOFF | `Workspace/Claude outputs/*.mp4`, `Workspace/Projects/Video/pipeline` | пайплайн генерации роликов |

## Готовые проекты (код, который можно переиспользовать)
| Проект | Путь | Что внутри / что взять |
|---|---|---|
| **OGE Math Bot** | `Projects/OGE Math Bot/oge_math_bot_windows_ready/oge_math_bot/app` | ~3.5k строк: тренировка по заданиям, проверка ответов, пробники, статистика, подписка, **платежи**, админка, репозитории задач/юзеров. **Главный донор для любых ботов с заданиями (SAT, ЕГЭ, ОГЭ)** |
| Autobox | `Projects/Autobox` | Telegram Mini App записи в автосервис/шиномонтаж, один `index.html`, конфиг клиента в `window.AUTOBOX_CONFIG`, папка `leads/`. Донор для B2B-ботов локального бизнеса |
| WordFlash (@engslearnbot) | `Projects/WordFlash` | Quizlet-бот: уроки, карточки, отчёты. Есть тесты, Dockerfile, railway.json. Донор для «учебных» ботов |
| EVOLUNE | `Projects/EVOLUNE` | бот + Mini App личного роста, alembic, docker-compose, webapp. Донор для Mini App и голосового ввода |
| NHL-REVIVAL / -partner | `Projects/NHL-REVIVAL*` | PvP карточный бот, партнёрское API, миграции. Боевой — только PR |
| NHLPROJECT / FACEOFF | `Projects/NHL Cards`, `Projects/TESTBOTEL` | экономика карточек, кланы, турниры, ranked, Mini App игра. Боевой — только PR |
| FACEOFF-Mod | `Projects/FACEOFF-Mod` | бот-модератор чата: ранги, наказания. Донор для модерации |
| KHL hockey_league_bot | `Projects/KHL` | хоккейная лига |
| Telegram Bulk Client | `Projects/Telegram Bulk Client` | Electron/React, мультиаккаунт |
| Nox | `Projects/Nox` | голосовой ассистент для Windows |
| voice2mp3 | `Projects/voice2mp3` | бот конвертации голосовых в mp3 |
| Puck General Events | `Projects/Puck General Events` | ивенты, есть сборка под Windows |
| Nexcore site | `Projects/Nexcore/nexcore_site_ready` | сайт студии |
| Accounting Project | `Projects/Accounting Project` | backend + mvp + отчёты |

## Не трогать никогда
- `Workspace/Secrets/` — токены и ключи. Не читать, не листать, не копировать.
- `Workspace/Backups/`, `Workspace/Railway/` — бэкапы боевых БД и патчи прода.
