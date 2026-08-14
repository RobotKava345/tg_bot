import logging

import aiosqlite

from config import DB_NAME


logger = logging.getLogger(__name__)


# ============================================================
# CREATE
# ============================================================

async def create_role(
    chat_id: int,
    name: str,
    description: str | None = None,
) -> int | None:
    """
    Создаёт новую роль.

    Возвращает:
        ID созданной роли
        None - если роль создать не удалось.

    В одном чате две роли с одинаковым названием
    существовать не могут.
    """

    name = name.strip()

    if not name:
        return None

    try:
        async with aiosqlite.connect(DB_NAME) as db:

            cursor = await db.execute(
                """
                INSERT INTO roles
                (
                    chat_id,
                    name,
                    description
                )
                VALUES (?, ?, ?)
                """,
                (
                    chat_id,
                    name,
                    description,
                ),
            )

            await db.commit()

            role_id = cursor.lastrowid

            logger.info(
                "Создана роль '%s' "
                "(ID=%s, chat_id=%s)",
                name,
                role_id,
                chat_id,
            )

            return role_id

    except aiosqlite.IntegrityError:
        logger.warning(
            "Роль '%s' уже существует "
            "в чате %s",
            name,
            chat_id,
        )

        return None

    except Exception as e:
        logger.error(
            "Ошибка создания роли '%s' "
            "в чате %s: %s",
            name,
            chat_id,
            e,
        )

        return None


# ============================================================
# GET ALL
# ============================================================

async def get_roles(
    chat_id: int,
) -> list[dict]:
    """
    Возвращает все активные роли чата.
    """

    async with aiosqlite.connect(DB_NAME) as db:

        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT
                id,
                chat_id,
                name,
                description,
                active,
                created_at,
                updated_at
            FROM roles
            WHERE chat_id = ?
              AND active = 1
            ORDER BY id ASC
            """,
            (
                chat_id,
            ),
        )

        rows = await cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]


# ============================================================
# GET ALL INCLUDING INACTIVE
# ============================================================

async def get_all_roles(
    chat_id: int,
) -> list[dict]:
    """
    Возвращает все роли чата,
    включая отключённые.
    """

    async with aiosqlite.connect(DB_NAME) as db:

        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT
                id,
                chat_id,
                name,
                description,
                active,
                created_at,
                updated_at
            FROM roles
            WHERE chat_id = ?
            ORDER BY id ASC
            """,
            (
                chat_id,
            ),
        )

        rows = await cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]


# ============================================================
# GET BY ID
# ============================================================

async def get_role(
    chat_id: int,
    role_id: int,
) -> dict | None:
    """
    Возвращает конкретную роль.
    """

    async with aiosqlite.connect(DB_NAME) as db:

        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT
                id,
                chat_id,
                name,
                description,
                active,
                created_at,
                updated_at
            FROM roles
            WHERE chat_id = ?
              AND id = ?
            LIMIT 1
            """,
            (
                chat_id,
                role_id,
            ),
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        return dict(row)


# ============================================================
# GET BY NAME
# ============================================================

async def get_role_by_name(
    chat_id: int,
    name: str,
) -> dict | None:
    """
    Ищет роль по названию.
    """

    name = name.strip()

    if not name:
        return None

    async with aiosqlite.connect(DB_NAME) as db:

        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT
                id,
                chat_id,
                name,
                description,
                active,
                created_at,
                updated_at
            FROM roles
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

        return dict(row)


# ============================================================
# SEARCH
# ============================================================

async def search_roles(
    chat_id: int,
    query: str,
) -> list[dict]:
    """
    Ищет роли по названию или описанию.
    """

    query = query.strip()

    if not query:
        return await get_roles(chat_id)

    pattern = f"%{query}%"

    async with aiosqlite.connect(DB_NAME) as db:

        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT
                id,
                chat_id,
                name,
                description,
                active,
                created_at,
                updated_at
            FROM roles
            WHERE chat_id = ?
              AND active = 1
              AND (
                    name LIKE ?
                    OR description LIKE ?
              )
            ORDER BY id ASC
            """,
            (
                chat_id,
                pattern,
                pattern,
            ),
        )

        rows = await cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]


# ============================================================
# UPDATE
# ============================================================

async def update_role(
    chat_id: int,
    role_id: int,
    name: str,
    description: str | None = None,
) -> bool:
    """
    Полностью изменяет роль.
    """

    name = name.strip()

    if not name:
        return False

    try:
        async with aiosqlite.connect(DB_NAME) as db:

            cursor = await db.execute(
                """
                UPDATE roles
                SET
                    name = ?,
                    description = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE chat_id = ?
                  AND id = ?
                """,
                (
                    name,
                    description,
                    chat_id,
                    role_id,
                ),
            )

            await db.commit()

            if cursor.rowcount > 0:
                logger.info(
                    "Изменена роль ID=%s "
                    "в чате %s",
                    role_id,
                    chat_id,
                )

            return cursor.rowcount > 0

    except aiosqlite.IntegrityError:
        logger.warning(
            "Нельзя переименовать роль: "
            "'%s' уже существует "
            "в чате %s",
            name,
            chat_id,
        )

        return False

    except Exception as e:
        logger.error(
            "Ошибка изменения роли %s "
            "в чате %s: %s",
            role_id,
            chat_id,
            e,
        )

        return False


# ============================================================
# UPDATE NAME
# ============================================================

async def update_role_name(
    chat_id: int,
    role_id: int,
    name: str,
) -> bool:
    """
    Изменяет только название роли.
    """

    name = name.strip()

    if not name:
        return False

    try:
        async with aiosqlite.connect(DB_NAME) as db:

            cursor = await db.execute(
                """
                UPDATE roles
                SET
                    name = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE chat_id = ?
                  AND id = ?
                """,
                (
                    name,
                    chat_id,
                    role_id,
                ),
            )

            await db.commit()

            return cursor.rowcount > 0

    except aiosqlite.IntegrityError:
        logger.warning(
            "Роль '%s' уже существует "
            "в чате %s",
            name,
            chat_id,
        )

        return False

    except Exception as e:
        logger.error(
            "Ошибка изменения названия "
            "роли %s: %s",
            role_id,
            e,
        )

        return False


# ============================================================
# UPDATE DESCRIPTION
# ============================================================

async def update_role_description(
    chat_id: int,
    role_id: int,
    description: str | None,
) -> bool:
    """
    Изменяет только описание роли.
    """

    try:
        async with aiosqlite.connect(DB_NAME) as db:

            cursor = await db.execute(
                """
                UPDATE roles
                SET
                    description = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE chat_id = ?
                  AND id = ?
                """,
                (
                    description,
                    chat_id,
                    role_id,
                ),
            )

            await db.commit()

            return cursor.rowcount > 0

    except Exception as e:
        logger.error(
            "Ошибка изменения описания "
            "роли %s: %s",
            role_id,
            e,
        )

        return False


# ============================================================
# ENABLE / DISABLE
# ============================================================

async def set_role_active(
    chat_id: int,
    role_id: int,
    active: bool,
) -> bool:
    """
    Включает или отключает роль.

    Это предпочтительнее физического удаления,
    если роль уже используется участниками.
    """

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            """
            UPDATE roles
            SET
                active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE chat_id = ?
              AND id = ?
            """,
            (
                1 if active else 0,
                chat_id,
                role_id,
            ),
        )

        await db.commit()

        return cursor.rowcount > 0


# ============================================================
# EXISTS
# ============================================================

async def role_exists(
    chat_id: int,
    role_id: int,
) -> bool:
    """
    Проверяет существование роли.
    """

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            """
            SELECT 1
            FROM roles
            WHERE chat_id = ?
              AND id = ?
            LIMIT 1
            """,
            (
                chat_id,
                role_id,
            ),
        )

        row = await cursor.fetchone()

        return row is not None


# ============================================================
# COUNT
# ============================================================

async def count_roles(
    chat_id: int,
) -> int:
    """
    Возвращает количество активных ролей.
    """

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM roles
            WHERE chat_id = ?
              AND active = 1
            """,
            (
                chat_id,
            ),
        )

        row = await cursor.fetchone()

        return row[0] if row else 0


# ============================================================
# COUNT USAGE
# ============================================================

async def count_role_usage(
    chat_id: int,
    role_id: int,
) -> int:
    """
    Возвращает количество карточек участников,
    которым назначена эта роль.
    """

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM member_profiles
            WHERE chat_id = ?
              AND role_id = ?
            """,
            (
                chat_id,
                role_id,
            ),
        )

        row = await cursor.fetchone()

        return row[0] if row else 0


# ============================================================
# DELETE
# ============================================================

async def delete_role(
    chat_id: int,
    role_id: int,
) -> bool:
    """
    Физически удаляет роль.

    Перед удалением желательно проверить
    count_role_usage().
    """

    usage = await count_role_usage(
        chat_id,
        role_id,
    )

    if usage > 0:
        logger.warning(
            "Нельзя удалить роль ID=%s "
            "в чате %s: используется "
            "в %s карточках",
            role_id,
            chat_id,
            usage,
        )

        return False

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            """
            DELETE FROM roles
            WHERE chat_id = ?
              AND id = ?
            """,
            (
                chat_id,
                role_id,
            ),
        )

        await db.commit()

        if cursor.rowcount > 0:
            logger.info(
                "Удалена роль ID=%s "
                "из чата %s",
                role_id,
                chat_id,
            )

        return cursor.rowcount > 0