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

async def create_rank(
    legion_id: int,
    name: str,
    points_required: int = 0,
    description: str | None = None,
) -> int:
    pool = get_pool()
    rank_id = await pool.fetchval(
        """
        INSERT INTO ranks (legion_id, name, points_required, description)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        legion_id, name, points_required, description,
    )
    logger.info(
        "Создано звание '%s' (ID=%s, legion_id=%s)",
        name, rank_id, legion_id,
    )
    return rank_id


# ============================================================
# GET ONE
# ============================================================

async def get_rank(rank_id: int, legion_id: int):
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, legion_id, name, points_required, description
        FROM ranks
        WHERE id = $1 AND legion_id = $2
        """,
        rank_id, legion_id,
    )
    return dict(row) if row else None


# ============================================================
# GET ALL
# ============================================================

async def get_ranks(legion_id: int):
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT id, legion_id, name, points_required, description
        FROM ranks
        WHERE legion_id = $1
        ORDER BY points_required ASC, id ASC
        """,
        legion_id,
    )
    return [dict(row) for row in rows]


# ============================================================
# GET BY NAME
# ============================================================

async def get_rank_by_name(legion_id: int, name: str):
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, legion_id, name, points_required, description
        FROM ranks
        WHERE legion_id = $1 AND name = $2
        LIMIT 1
        """,
        legion_id, name,
    )
    return dict(row) if row else None


# ============================================================
# EXISTS
# ============================================================

async def rank_exists(legion_id: int, rank_id: int) -> bool:
    pool = get_pool()
    row = await pool.fetchval(
        """
        SELECT 1 FROM ranks
        WHERE id = $1 AND legion_id = $2
        LIMIT 1
        """,
        rank_id, legion_id,
    )
    return row is not None


# ============================================================
# UPDATE
# ============================================================

async def update_rank(
    legion_id: int,
    rank_id: int,
    name: str,
    points_required: int = 0,
    description: str | None = None,
) -> bool:
    pool = get_pool()
    status = await pool.execute(
        """
        UPDATE ranks
        SET name = $1, points_required = $2, description = $3
        WHERE id = $4 AND legion_id = $5
        """,
        name, points_required, description, rank_id, legion_id,
    )
    updated = _parse_rowcount(status) > 0
    if updated:
        logger.info("Обновлено звание ID=%s (legion_id=%s)", rank_id, legion_id)
    return updated


# ============================================================
# UPDATE NAME
# ============================================================

async def update_rank_name(legion_id: int, rank_id: int, name: str) -> bool:
    pool = get_pool()
    status = await pool.execute(
        """
        UPDATE ranks SET name = $1
        WHERE id = $2 AND legion_id = $3
        """,
        name, rank_id, legion_id,
    )
    return _parse_rowcount(status) > 0


# ============================================================
# UPDATE POINTS
# ============================================================

async def update_rank_points(legion_id: int, rank_id: int, points_required: int) -> bool:
    if points_required < 0:
        raise ValueError("Количество очков не может быть отрицательным")

    pool = get_pool()
    status = await pool.execute(
        """
        UPDATE ranks SET points_required = $1
        WHERE id = $2 AND legion_id = $3
        """,
        points_required, rank_id, legion_id,
    )
    return _parse_rowcount(status) > 0


# ============================================================
# UPDATE DESCRIPTION
# ============================================================

async def update_rank_description(
    legion_id: int,
    rank_id: int,
    description: str | None,
) -> bool:
    pool = get_pool()
    status = await pool.execute(
        """
        UPDATE ranks SET description = $1
        WHERE id = $2 AND legion_id = $3
        """,
        description, rank_id, legion_id,
    )
    return _parse_rowcount(status) > 0


# ============================================================
# DELETE
# ============================================================

async def delete_rank(legion_id: int, rank_id: int) -> bool:
    pool = get_pool()
    status = await pool.execute(
        """
        DELETE FROM ranks
        WHERE id = $1 AND legion_id = $2
        """,
        rank_id, legion_id,
    )
    deleted = _parse_rowcount(status) > 0
    if deleted:
        logger.info("Удалено звание ID=%s из legion_id=%s", rank_id, legion_id)
    return deleted


# ============================================================
# COUNT
# ============================================================

async def count_ranks(legion_id: int) -> int:
    pool = get_pool()
    row = await pool.fetchval(
        "SELECT COUNT(*) FROM ranks WHERE legion_id = $1",
        legion_id,
    )
    return row or 0