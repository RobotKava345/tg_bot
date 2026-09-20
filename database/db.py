import logging

from database.pool import get_pool

logger = logging.getLogger(__name__)


async def init_db() -> None:
    pool = get_pool()

    async with pool.acquire() as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_users (
                chat_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                first_seen TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, user_id)
            )
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_seen_users_chat
            ON seen_users(chat_id)
            """
        )

    logger.info("Database schema initialized")


async def add_user(chat_id: int, user_id: int) -> None:
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO seen_users (chat_id, user_id)
        VALUES ($1, $2)
        ON CONFLICT (chat_id, user_id) DO NOTHING
        """,
        chat_id,
        user_id,
    )


async def get_seen_users(chat_id: int) -> list[int]:
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT user_id FROM seen_users WHERE chat_id = $1",
        chat_id,
    )
    return [row["user_id"] for row in rows]


async def count_seen_users(chat_id: int) -> int:
    pool = get_pool()
    return int(
        await pool.fetchval(
            "SELECT COUNT(*) FROM seen_users WHERE chat_id = $1",
            chat_id,
        )
        or 0
    )
