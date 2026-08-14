import logging

import aiosqlite

from config import DB_NAME


logger = logging.getLogger(__name__)


# ============================================================
# CREATE
# ============================================================

async def create_rank(
    legion_id: int,
    name: str,
    points_required: int = 0,
    description: str | None = None,
) -> int:
    """
    Создаёт новое звание для легиона.

    Возвращает ID созданного звания.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            INSERT INTO ranks
            (
                legion_id,
                name,
                points_required,
                description
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                legion_id,
                name,
                points_required,
                description,
            ),
        )

        await db.commit()

        rank_id = cursor.lastrowid

        logger.info(
            "Создано звание '%s' (ID=%s, legion_id=%s)",
            name,
            rank_id,
            legion_id,
        )

        return rank_id


# ============================================================
# GET ONE
# ============================================================

async def get_rank(
    rank_id: int,
    legion_id: int,
):
    """
    Возвращает одно звание конкретного легиона.

    Если звание не найдено - None.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT
                id,
                legion_id,
                name,
                points_required,
                description
            FROM ranks
            WHERE id = ?
              AND legion_id = ?
            """,
            (
                rank_id,
                legion_id,
            ),
        )

        row = await cursor.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "legion_id": row[1],
        "name": row[2],
        "points_required": row[3],
        "description": row[4],
    }


# ============================================================
# GET ALL
# ============================================================

async def get_ranks(
    legion_id: int,
):
    """
    Возвращает все звания конкретного легиона.

    Сортировка:
    1. по необходимому количеству очков;
    2. затем по ID.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT
                id,
                legion_id,
                name,
                points_required,
                description
            FROM ranks
            WHERE legion_id = ?
            ORDER BY points_required ASC, id ASC
            """,
            (legion_id,),
        )

        rows = await cursor.fetchall()

    return [
        {
            "id": row[0],
            "legion_id": row[1],
            "name": row[2],
            "points_required": row[3],
            "description": row[4],
        }
        for row in rows
    ]


# ============================================================
# GET BY NAME
# ============================================================

async def get_rank_by_name(
    legion_id: int,
    name: str,
):
    """
    Ищет звание по названию внутри конкретного легиона.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT
                id,
                legion_id,
                name,
                points_required,
                description
            FROM ranks
            WHERE legion_id = ?
              AND name = ?
            LIMIT 1
            """,
            (
                legion_id,
                name,
            ),
        )

        row = await cursor.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "legion_id": row[1],
        "name": row[2],
        "points_required": row[3],
        "description": row[4],
    }


# ============================================================
# EXISTS
# ============================================================

async def rank_exists(
    legion_id: int,
    rank_id: int,
) -> bool:
    """
    Проверяет существование звания внутри легиона.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT 1
            FROM ranks
            WHERE id = ?
              AND legion_id = ?
            LIMIT 1
            """,
            (
                rank_id,
                legion_id,
            ),
        )

        row = await cursor.fetchone()

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
    """
    Полностью обновляет звание.

    Возвращает:
        True  - звание обновлено
        False - звание не найдено
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            UPDATE ranks
            SET
                name = ?,
                points_required = ?,
                description = ?
            WHERE id = ?
              AND legion_id = ?
            """,
            (
                name,
                points_required,
                description,
                rank_id,
                legion_id,
            ),
        )

        await db.commit()

    if cursor.rowcount > 0:
        logger.info(
            "Обновлено звание ID=%s (legion_id=%s)",
            rank_id,
            legion_id,
        )

    return cursor.rowcount > 0


# ============================================================
# UPDATE NAME
# ============================================================

async def update_rank_name(
    legion_id: int,
    rank_id: int,
    name: str,
) -> bool:
    """
    Изменяет только название звания.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            UPDATE ranks
            SET name = ?
            WHERE id = ?
              AND legion_id = ?
            """,
            (
                name,
                rank_id,
                legion_id,
            ),
        )

        await db.commit()

    return cursor.rowcount > 0


# ============================================================
# UPDATE POINTS
# ============================================================

async def update_rank_points(
    legion_id: int,
    rank_id: int,
    points_required: int,
) -> bool:
    """
    Изменяет необходимое количество очков.
    """

    if points_required < 0:
        raise ValueError(
            "Количество очков не может быть отрицательным"
        )

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            UPDATE ranks
            SET points_required = ?
            WHERE id = ?
              AND legion_id = ?
            """,
            (
                points_required,
                rank_id,
                legion_id,
            ),
        )

        await db.commit()

    return cursor.rowcount > 0


# ============================================================
# UPDATE DESCRIPTION
# ============================================================

async def update_rank_description(
    legion_id: int,
    rank_id: int,
    description: str | None,
) -> bool:
    """
    Изменяет описание звания.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            UPDATE ranks
            SET description = ?
            WHERE id = ?
              AND legion_id = ?
            """,
            (
                description,
                rank_id,
                legion_id,
            ),
        )

        await db.commit()

    return cursor.rowcount > 0


# ============================================================
# DELETE
# ============================================================

async def delete_rank(
    legion_id: int,
    rank_id: int,
) -> bool:
    """
    Удаляет звание из конкретного легиона.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            DELETE FROM ranks
            WHERE id = ?
              AND legion_id = ?
            """,
            (
                rank_id,
                legion_id,
            ),
        )

        await db.commit()

    if cursor.rowcount > 0:
        logger.info(
            "Удалено звание ID=%s из legion_id=%s",
            rank_id,
            legion_id,
        )

    return cursor.rowcount > 0


# ============================================================
# COUNT
# ============================================================

async def count_ranks(
    legion_id: int,
) -> int:
    """
    Возвращает количество званий конкретного легиона.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM ranks
            WHERE legion_id = ?
            """,
            (legion_id,),
        )

        row = await cursor.fetchone()

    return row[0] if row else 0