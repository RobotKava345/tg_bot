import logging
import aiosqlite

from config import DB_NAME

logger = logging.getLogger(__name__)


# ============================================================
# Создание таблицы
# ============================================================

async def init_statuses_table():
    """
    Создаёт таблицу статусов, если она ещё не существует.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS statuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chat_id, name)
            )
            """
        )

        await db.commit()


# ============================================================
# Создание статуса
# ============================================================

async def create_status(
    chat_id: int,
    name: str,
    description: str | None = None,
) -> int | None:
    """
    Создаёт новый статус.

    Возвращает ID созданного статуса.
    Если такой статус уже существует - None.
    """

    name = name.strip()

    if not name:
        return None

    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                """
                INSERT INTO statuses (
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

            return cursor.lastrowid

    except aiosqlite.IntegrityError:
        logger.warning(
            "Статус '%s' уже существует в чате %s",
            name,
            chat_id,
        )

        return None

    except Exception as e:
        logger.error(
            "Ошибка создания статуса '%s' "
            "в чате %s: %s",
            name,
            chat_id,
            e,
        )

        return None


# ============================================================
# Получение статуса
# ============================================================

async def get_status(
    chat_id: int,
    status_id: int,
) -> dict | None:
    """
    Получает статус по ID.
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
                created_at
            FROM statuses
            WHERE chat_id = ?
              AND id = ?
            """,
            (
                chat_id,
                status_id,
            ),
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        return dict(row)


# ============================================================
# Получение всех статусов
# ============================================================

async def get_statuses(
    chat_id: int,
) -> list[dict]:
    """
    Возвращает все статусы чата.
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
                created_at
            FROM statuses
            WHERE chat_id = ?
            ORDER BY id ASC
            """,
            (chat_id,),
        )

        rows = await cursor.fetchall()

        return [dict(row) for row in rows]


# ============================================================
# Поиск статусов
# ============================================================

async def search_statuses(
    chat_id: int,
    query: str,
) -> list[dict]:
    """
    Ищет статусы по названию или описанию.
    """

    query = query.strip()

    if not query:
        return await get_statuses(chat_id)

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
                created_at
            FROM statuses
            WHERE chat_id = ?
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

        return [dict(row) for row in rows]


# ============================================================
# Изменение статуса
# ============================================================

async def update_status(
    chat_id: int,
    status_id: int,
    name: str,
    description: str | None = None,
) -> bool:
    """
    Изменяет существующий статус.
    """

    name = name.strip()

    if not name:
        return False

    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                """
                UPDATE statuses
                SET
                    name = ?,
                    description = ?
                WHERE chat_id = ?
                  AND id = ?
                """,
                (
                    name,
                    description,
                    chat_id,
                    status_id,
                ),
            )

            await db.commit()

            return cursor.rowcount > 0

    except aiosqlite.IntegrityError:
        logger.warning(
            "Нельзя переименовать статус: "
            "'%s' уже существует в чате %s",
            name,
            chat_id,
        )

        return False

    except Exception as e:
        logger.error(
            "Ошибка изменения статуса %s "
            "в чате %s: %s",
            status_id,
            chat_id,
            e,
        )

        return False


# ============================================================
# Удаление статуса
# ============================================================

async def delete_status(
    chat_id: int,
    status_id: int,
) -> bool:
    """
    Удаляет статус.

    ВАЖНО:
    Перед удалением нужно проверить,
    используется ли этот статус в member_profiles.
    """

    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                """
                DELETE FROM statuses
                WHERE chat_id = ?
                  AND id = ?
                """,
                (
                    chat_id,
                    status_id,
                ),
            )

            await db.commit()

            return cursor.rowcount > 0

    except Exception as e:
        logger.error(
            "Ошибка удаления статуса %s "
            "в чате %s: %s",
            status_id,
            chat_id,
            e,
        )

        return False


# ============================================================
# Проверка существования
# ============================================================

async def status_exists(
    chat_id: int,
    status_id: int,
) -> bool:
    """
    Проверяет существование статуса.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT 1
            FROM statuses
            WHERE chat_id = ?
              AND id = ?
            LIMIT 1
            """,
            (
                chat_id,
                status_id,
            ),
        )

        row = await cursor.fetchone()

        return row is not None


# ============================================================
# Проверка использования статуса
# ============================================================

async def count_status_usage(
    chat_id: int,
    status_id: int,
) -> int:
    """
    Возвращает количество карточек участников,
    использующих данный статус.

    Предполагается, что member_profiles.status_id
    хранит ID статуса.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM member_profiles
            WHERE chat_id = ?
              AND status_id = ?
            """,
            (
                chat_id,
                status_id,
            ),
        )

        row = await cursor.fetchone()

        return row[0] if row else 0