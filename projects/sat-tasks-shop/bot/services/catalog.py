"""Чистая логика каталога: сид тем SAT и разбор админ-команд."""

import re
from dataclasses import dataclass

CODE_RE = re.compile(r"^[A-Za-z0-9._-]{1,32}$")


@dataclass(frozen=True)
class TopicSeed:
    code: str
    section: str
    title: str
    tasks_count: int


# Снимок Workspace/SAT (2026-10-22): коды тем College Board, число заданий — из имён Zadaniya_1-N.pdf
SAT_TOPICS: list[TopicSeed] = [
    TopicSeed("H.A", "Algebra", "Линейные уравнения с одной переменной", 100),
    TopicSeed("H.B", "Algebra", "Линейные функции", 170),
    TopicSeed("H.C", "Algebra", "Линейные уравнения с двумя переменными", 130),
    TopicSeed("H.D", "Algebra", "Системы двух линейных уравнений", 126),
    TopicSeed("H.E", "Algebra", "Линейные неравенства", 78),
    TopicSeed("P.A", "Advanced Math", "Равносильные выражения", 116),
    TopicSeed("P.B", "Advanced Math", "Нелинейные уравнения и системы", 165),
    TopicSeed("P.C", "Advanced Math", "Нелинейные функции", 259),
    TopicSeed("Q.A", "Problem-Solving and Data Analysis", "Отношения, скорости, пропорции, единицы", 93),
    TopicSeed("Q.B", "Problem-Solving and Data Analysis", "Проценты", 84),
    TopicSeed("Q.C", "Problem-Solving and Data Analysis", "Данные с одной переменной", 84),
    TopicSeed("Q.D", "Problem-Solving and Data Analysis", "Данные с двумя переменными", 71),
    TopicSeed("Q.E", "Problem-Solving and Data Analysis", "Вероятность", 49),
    TopicSeed("Q.F", "Problem-Solving and Data Analysis", "Выводы по выборке и погрешность", 28),
    TopicSeed("Q.G", "Problem-Solving and Data Analysis", "Оценка статистических утверждений", 12),
    TopicSeed("S.A", "Geometry and Trigonometry", "Площадь и объём", 110),
    TopicSeed("S.B", "Geometry and Trigonometry", "Прямые, углы, треугольники", 102),
    TopicSeed("S.C", "Geometry and Trigonometry", "Прямоугольные треугольники и тригонометрия", 69),
    TopicSeed("S.D", "Geometry and Trigonometry", "Окружности", 67),
]


class ParseError(ValueError):
    pass


def is_valid_code(code: str) -> bool:
    return bool(CODE_RE.match(code))


def parse_addtopic(args: str | None) -> TopicSeed:
    """`CODE | Раздел | Название | Кол-во` → TopicSeed. Бросает ParseError с понятным текстом."""
    parts = [p.strip() for p in (args or "").split("|")]
    if len(parts) != 4 or not all(parts):
        raise ParseError("Нужно 4 поля через «|»: CODE | Раздел | Название | Кол-во")
    code, section, title, count_raw = parts
    if not is_valid_code(code):
        raise ParseError("Код темы: латиница, цифры, «.», «_», «-», до 32 символов")
    if not count_raw.isdigit():
        raise ParseError("Кол-во заданий — целое число")
    if len(section) > 64 or len(title) > 128:
        raise ParseError("Слишком длинные раздел (≤64) или название (≤128)")
    return TopicSeed(code, section, title, int(count_raw))


def parse_code(args: str | None) -> str:
    code = (args or "").strip()
    if not is_valid_code(code):
        raise ParseError("Укажи код темы, например: H.A")
    return code
