import logging

from database.pool import get_pool

logger = logging.getLogger(__name__)


def _parse_rowcount(status: str) -> int:
    try:
        return int(status.split()[-1])
    except (ValueError, IndexError):
        return 0


# ============================================================
# CREATE
# ============================================================

async def create_legion(
    chat_id: int,
    name: str,
    primarch_id: int | None = None,
    description: str | None = None,
) -> int:
    pool = get_pool()

    legion_id = await pool.fetchval(
        """
        INSERT INTO legions (chat_id, name, primarch_id, description)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        chat_id, name, primarch_id, description,
    )

    logger.info(
        "Создан легион '%s' (ID=%s, chat_id=%s)",
        name, legion_id, chat_id,
    )
    return legion_id


# ============================================================
# GET ONE
# ============================================================

async def get_legion(legion_id: int, chat_id: int):
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, chat_id, name, primarch_id, description
        FROM legions
        WHERE id = $1 AND chat_id = $2
        """,
        legion_id, chat_id,
    )
    return dict(row) if row else None


# ============================================================
# GET ALL
# ============================================================

async def get_legions(chat_id: int):
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT id, chat_id, name, primarch_id, description
        FROM legions
        WHERE chat_id = $1
        ORDER BY id ASC
        """,
        chat_id,
    )
    return [dict(row) for row in rows]


# ============================================================
# EXISTS
# ============================================================

async def legion_exists(chat_id: int, legion_id: int) -> bool:
    pool = get_pool()
    row = await pool.fetchval(
        """
        SELECT 1 FROM legions
        WHERE id = $1 AND chat_id = $2
        LIMIT 1
        """,
        legion_id, chat_id,
    )
    return row is not None


# ============================================================
# GET BY NAME
# ============================================================

async def get_legion_by_name(chat_id: int, name: str):
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, chat_id, name, primarch_id, description
        FROM legions
        WHERE chat_id = $1 AND name = $2
        LIMIT 1
        """,
        chat_id, name,
    )
    return dict(row) if row else None


# ============================================================
# UPDATE
# ============================================================

async def update_legion(
    chat_id: int,
    legion_id: int,
    name: str,
    primarch_id: int | None = None,
    description: str | None = None,
) -> bool:
    pool = get_pool()
    status = await pool.execute(
        """
        UPDATE legions
        SET name = $1, primarch_id = $2, description = $3
        WHERE id = $4 AND chat_id = $5
        """,
        name, primarch_id, description, legion_id, chat_id,
    )
    updated = _parse_rowcount(status) > 0
    if updated:
        logger.info("Обновлён легион ID=%s в chat_id=%s", legion_id, chat_id)
    return updated


# ============================================================
# UPDATE NAME
# ============================================================

async def update_legion_name(chat_id: int, legion_id: int, name: str) -> bool:
    pool = get_pool()
    status = await pool.execute(
        """
        UPDATE legions SET name = $1
        WHERE id = $2 AND chat_id = $3
        """,
        name, legion_id, chat_id,
    )
    return _parse_rowcount(status) > 0


# ============================================================
# UPDATE DESCRIPTION
# ============================================================

async def update_legion_description(
    chat_id: int,
    legion_id: int,
    description: str | None,
) -> bool:
    pool = get_pool()
    status = await pool.execute(
        """
        UPDATE legions SET description = $1
        WHERE id = $2 AND chat_id = $3
        """,
        description, legion_id, chat_id,
    )
    return _parse_rowcount(status) > 0


# ============================================================
# SET PRIMARCH
# ============================================================

async def set_primarch(
    chat_id: int,
    legion_id: int,
    primarch_id: int | None,
) -> bool:
    pool = get_pool()
    status = await pool.execute(
        """
        UPDATE legions SET primarch_id = $1
        WHERE id = $2 AND chat_id = $3
        """,
        primarch_id, legion_id, chat_id,
    )
    updated = _parse_rowcount(status) > 0
    if updated:
        logger.info(
            "Примарх легиона ID=%s изменён на user_id=%s",
            legion_id, primarch_id,
        )
    return updated


# ============================================================
# GET BY PRIMARCH
# ============================================================

async def get_legion_by_primarch(chat_id: int, primarch_id: int):
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, chat_id, name, primarch_id, description
        FROM legions
        WHERE chat_id = $1 AND primarch_id = $2
        LIMIT 1
        """,
        chat_id, primarch_id,
    )
    return dict(row) if row else None


# ============================================================
# DELETE
# ============================================================

async def delete_legion(chat_id: int, legion_id: int) -> bool:
    pool = get_pool()
    status = await pool.execute(
        """
        DELETE FROM legions
        WHERE id = $1 AND chat_id = $2
        """,
        legion_id, chat_id,
    )
    deleted = _parse_rowcount(status) > 0
    if deleted:
        logger.info("Удалён легион ID=%s из chat_id=%s", legion_id, chat_id)
    return deleted


# ============================================================
# COUNT
# ============================================================

async def count_legions(chat_id: int) -> int:
    pool = get_pool()
    row = await pool.fetchval(
        "SELECT COUNT(*) FROM legions WHERE chat_id = $1",
        chat_id,
    )
    return row or 0