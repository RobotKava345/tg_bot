"""
Единый пул соединений asyncpg на весь бот.

Раньше каждая функция в database/*.py открывала своё соединение
через `async with aiosqlite.connect(DB_NAME)`. Для локального файла
SQLite это дёшево. Для Postgres на Render это сетевое соединение —
открывать новое на каждый запрос дорого и медленно.

Вместо этого один раз при старте бота создаём пул (несколько уже
открытых соединений, переиспользуемых между запросами), и все
database/*.py берут соединение из него.
"""

import asyncpg

from config import DATABASE_URL

_pool: asyncpg.Pool | None = None


async def init_pool():
    global _pool
    if _pool is not None:
        return _pool

    _pool = await asyncpg.create_pool(
        dsn=DATABASE_URL,
        min_size=1,
        max_size=5,
        # Render Free Postgres может обрывать простаивающие соединения —
        # держим пул небольшим и просим asyncpg переподключаться при сбое.
        command_timeout=30,
    )
    return _pool


async def close_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError(
            "Пул соединений ещё не инициализирован. "
            "Убедись, что init_pool() вызван в main() до первого "
            "обращения к базе."
        )
    return _pool