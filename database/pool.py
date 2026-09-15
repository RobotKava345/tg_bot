import asyncpg
from config import DATABASE_URL

_pool = None


async def init_pool():
    global _pool

    _pool = await asyncpg.create_pool(
        dsn=DATABASE_URL,
        min_size=1,
        max_size=5,
        command_timeout=30,
        ssl="require",
    )


async def close_pool():
    global _pool

    if _pool:
        await _pool.close()


def get_pool():
    return _pool