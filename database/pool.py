import ssl

import asyncpg

from config import settings

_pool: asyncpg.Pool | None = None


def _ssl_context() -> ssl.SSLContext | None:
    if not settings.database_ssl:
        return None

    # Compatible with managed PostgreSQL providers that require TLS.
    # Certificate verification can be tightened for providers that
    # publish a CA certificate.
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


async def init_pool() -> None:
    global _pool

    if _pool is not None:
        return

    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=1,
        max_size=5,
        command_timeout=30,
        ssl=_ssl_context(),
    )


async def close_pool() -> None:
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized.")
    return _pool
