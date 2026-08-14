import logging

import aiosqlite

from config import DB_NAME


logger = logging.getLogger(__name__)


# ============================================================
# CREATE
# ============================================================

async def create_legion(
    chat_id: int,
    name: str,
    primarch_id: int | None = None,
    description: str | None = None,
) -> int:
    """
    Создаёт легион.

    Возвращает ID созданного легиона.

    primarch_id - Telegram ID пользователя, который является
    примархом данного легиона.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            INSERT INTO legions
            (
                chat_id,
                name,
                primarch_id,
                description
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                chat_id,
                name,
                primarch_id,
                description,
            ),
        )

        await db.commit()

        legion_id = cursor.lastrowid

        logger.info(
            "Создан легион '%s' (ID=%s, chat_id=%s)",
            name,
            legion_id,
            chat_id,
        )

        return legion_id


# ============================================================
# GET ONE
# ============================================================

async def get_legion(
    legion_id: int,
    chat_id: int,
):
    """
    Возвращает один легион.

    Возвращает:
        {
            "id": ...,
            "chat_id": ...,
            "name": ...,
            "primarch_id": ...,
            "description": ...
        }

    Если легион не найден - None.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT
                id,
                chat_id,
                name,
                primarch_id,
                description
            FROM legions
            WHERE id = ?
              AND chat_id = ?
            """,
            (
                legion_id,
                chat_id,
            ),
        )

        row = await cursor.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "chat_id": row[1],
        "name": row[2],
        "primarch_id": row[3],
        "description": row[4],
    }


# ============================================================
# GET ALL
# ============================================================

async def get_legions(
    chat_id: int,
):
    """
    Возвращает все легионы конкретного чата.

    Сортировка - по ID.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT
                id,
                chat_id,
                name,
                primarch_id,
                description
            FROM legions
            WHERE chat_id = ?
            ORDER BY id ASC
            """,
            (chat_id,),
        )

        rows = await cursor.fetchall()

    return [
        {
            "id": row[0],
            "chat_id": row[1],
            "name": row[2],
            "primarch_id": row[3],
            "description": row[4],
        }
        for row in rows
    ]


# ============================================================
# EXISTS
# ============================================================

async def legion_exists(
    chat_id: int,
    legion_id: int,
) -> bool:
    """
    Проверяет, существует ли легион в указанном чате.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT 1
            FROM legions
            WHERE id = ?
              AND chat_id = ?
            LIMIT 1
            """,
            (
                legion_id,
                chat_id,
            ),
        )

        row = await cursor.fetchone()

    return row is not None


# ============================================================
# GET BY NAME
# ============================================================

async def get_legion_by_name(
    chat_id: int,
    name: str,
):
    """
    Ищет легион по названию внутри конкретного чата.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT
                id,
                chat_id,
                name,
                primarch_id,
                description
            FROM legions
            WHERE chat_id = ?
              AND name = ?
            LIMIT 1
            """,
            (
                chat_id,
                name,
            ),
        )

        row = await cursor.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "chat_id": row[1],
        "name": row[2],
        "primarch_id": row[3],
        "description": row[4],
    }


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
    """
    Полностью обновляет данные легиона.

    Возвращает:
        True  - если легион обновлён
        False - если легион не найден в этом чате
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            UPDATE legions
            SET
                name = ?,
                primarch_id = ?,
                description = ?
            WHERE id = ?
              AND chat_id = ?
            """,
            (
                name,
                primarch_id,
                description,
                legion_id,
                chat_id,
            ),
        )

        await db.commit()

        updated = cursor.rowcount > 0

    if updated:
        logger.info(
            "Обновлён легион ID=%s в chat_id=%s",
            legion_id,
            chat_id,
        )

    return updated


# ============================================================
# UPDATE NAME
# ============================================================

async def update_legion_name(
    chat_id: int,
    legion_id: int,
    name: str,
) -> bool:
    """
    Изменяет только название легиона.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            UPDATE legions
            SET name = ?
            WHERE id = ?
              AND chat_id = ?
            """,
            (
                name,
                legion_id,
                chat_id,
            ),
        )

        await db.commit()

    return cursor.rowcount > 0


# ============================================================
# UPDATE DESCRIPTION
# ============================================================

async def update_legion_description(
    chat_id: int,
    legion_id: int,
    description: str | None,
) -> bool:
    """
    Изменяет описание легиона.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            UPDATE legions
            SET description = ?
            WHERE id = ?
              AND chat_id = ?
            """,
            (
                description,
                legion_id,
                chat_id,
            ),
        )

        await db.commit()

    return cursor.rowcount > 0


# ============================================================
# SET PRIMARCH
# ============================================================

async def set_primarch(
    chat_id: int,
    legion_id: int,
    primarch_id: int | None,
) -> bool:
    """
    Назначает примарха легиона.

    primarch_id=None снимает текущего примарха.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            UPDATE legions
            SET primarch_id = ?
            WHERE id = ?
              AND chat_id = ?
            """,
            (
                primarch_id,
                legion_id,
                chat_id,
            ),
        )

        await db.commit()

    if cursor.rowcount > 0:
        logger.info(
            "Примарх легиона ID=%s изменён на user_id=%s",
            legion_id,
            primarch_id,
        )

    return cursor.rowcount > 0


# ============================================================
# GET BY PRIMARCH
# ============================================================

async def get_legion_by_primarch(
    chat_id: int,
    primarch_id: int,
):
    """
    Возвращает легион, которым руководит указанный примарх.

    Если пользователь не является примархом ни одного легиона,
    возвращает None.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT
                id,
                chat_id,
                name,
                primarch_id,
                description
            FROM legions
            WHERE chat_id = ?
              AND primarch_id = ?
            LIMIT 1
            """,
            (
                chat_id,
                primarch_id,
            ),
        )

        row = await cursor.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "chat_id": row[1],
        "name": row[2],
        "primarch_id": row[3],
        "description": row[4],
    }


# ============================================================
# DELETE
# ============================================================

async def delete_legion(
    chat_id: int,
    legion_id: int,
) -> bool:
    """
    Удаляет легион.

    Вместе с ним SQLite удалит связанные звания,
    если FOREIGN KEY constraints включены.

    Возвращает:
        True  - удалён
        False - не найден
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            DELETE FROM legions
            WHERE id = ?
              AND chat_id = ?
            """,
            (
                legion_id,
                chat_id,
            ),
        )

        await db.commit()

    if cursor.rowcount > 0:
        logger.info(
            "Удалён легион ID=%s из chat_id=%s",
            legion_id,
            chat_id,
        )

    return cursor.rowcount > 0


# ============================================================
# COUNT
# ============================================================

async def count_legions(
    chat_id: int,
) -> int:
    """
    Возвращает количество легионов в чате.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM legions
            WHERE chat_id = ?
            """,
            (chat_id,),
        )

        row = await cursor.fetchone()

    return row[0] if row else 0