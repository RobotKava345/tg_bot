import logging

import aiosqlite

from config import DB_NAME


logger = logging.getLogger(__name__)


# ============================================================
# CREATE / GET
# ============================================================

async def create_member_profile(
    chat_id: int,
    user_id: int,
    display_name: str | None = None,
):
    """
    Создаёт карточку участника.

    Если карточка уже существует - ничего не делает.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO member_profiles
            (
                chat_id,
                user_id,
                display_name
            )
            VALUES (?, ?, ?)
            """,
            (
                chat_id,
                user_id,
                display_name,
            ),
        )

        await db.commit()


async def get_member_profile(
    chat_id: int,
    user_id: int,
):
    """
    Возвращает карточку конкретного участника.

    Формат результата:

    (
        chat_id,
        user_id,
        display_name,
        role_id,
        rank_id,
        legion_id,
        status_id,
        reputation,
        created_at,
        updated_at
    )

    Если карточки нет - возвращает None.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT
                chat_id,
                user_id,
                display_name,
                role_id,
                rank_id,
                legion_id,
                status_id,
                reputation,
                created_at,
                updated_at
            FROM member_profiles
            WHERE chat_id = ?
              AND user_id = ?
            """,
            (
                chat_id,
                user_id,
            ),
        )

        return await cursor.fetchone()


async def get_member_profiles(
    chat_id: int,
):
    """
    Возвращает все карточки участников указанного чата.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT
                chat_id,
                user_id,
                display_name,
                role_id,
                rank_id,
                legion_id,
                status_id,
                reputation,
                created_at,
                updated_at
            FROM member_profiles
            WHERE chat_id = ?
            ORDER BY user_id
            """,
            (chat_id,),
        )

        return await cursor.fetchall()


# ============================================================
# NAME
# ============================================================

async def update_member_name(
    chat_id: int,
    user_id: int,
    display_name: str,
):
    """
    Изменяет отображаемое имя участника.

    Если карточки ещё нет - она будет создана.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO member_profiles
            (
                chat_id,
                user_id,
                display_name
            )
            VALUES (?, ?, ?)

            ON CONFLICT(chat_id, user_id)
            DO UPDATE SET
                display_name = excluded.display_name,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                chat_id,
                user_id,
                display_name,
            ),
        )

        await db.commit()


# ============================================================
# ROLE
# ============================================================

async def update_member_role(
    chat_id: int,
    user_id: int,
    role_id: int | None,
):
    """
    Назначает или снимает роль.

    role_id=None означает снять роль.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO member_profiles
            (
                chat_id,
                user_id,
                role_id
            )
            VALUES (?, ?, ?)

            ON CONFLICT(chat_id, user_id)
            DO UPDATE SET
                role_id = excluded.role_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                chat_id,
                user_id,
                role_id,
            ),
        )

        await db.commit()


# ============================================================
# RANK
# ============================================================

async def update_member_rank(
    chat_id: int,
    user_id: int,
    rank_id: int | None,
):
    """
    Назначает или снимает звание.

    rank_id=None означает снять звание.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO member_profiles
            (
                chat_id,
                user_id,
                rank_id
            )
            VALUES (?, ?, ?)

            ON CONFLICT(chat_id, user_id)
            DO UPDATE SET
                rank_id = excluded.rank_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                chat_id,
                user_id,
                rank_id,
            ),
        )

        await db.commit()


# ============================================================
# LEGION
# ============================================================

async def update_member_legion(
    chat_id: int,
    user_id: int,
    legion_id: int | None,
):
    """
    Назначает или снимает легион.

    legion_id=None означает снять легион.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO member_profiles
            (
                chat_id,
                user_id,
                legion_id
            )
            VALUES (?, ?, ?)

            ON CONFLICT(chat_id, user_id)
            DO UPDATE SET
                legion_id = excluded.legion_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                chat_id,
                user_id,
                legion_id,
            ),
        )

        await db.commit()


# ============================================================
# STATUS
# ============================================================

async def update_member_status(
    chat_id: int,
    user_id: int,
    status_id: int | None,
):
    """
    Назначает или снимает статус.

    status_id=None означает снять статус.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO member_profiles
            (
                chat_id,
                user_id,
                status_id
            )
            VALUES (?, ?, ?)

            ON CONFLICT(chat_id, user_id)
            DO UPDATE SET
                status_id = excluded.status_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                chat_id,
                user_id,
                status_id,
            ),
        )

        await db.commit()


# ============================================================
# REPUTATION
# ============================================================

async def update_member_reputation(
    chat_id: int,
    user_id: int,
    reputation: int,
):
    """
    Устанавливает репутацию участника.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO member_profiles
            (
                chat_id,
                user_id,
                reputation
            )
            VALUES (?, ?, ?)

            ON CONFLICT(chat_id, user_id)
            DO UPDATE SET
                reputation = excluded.reputation,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                chat_id,
                user_id,
                reputation,
            ),
        )

        await db.commit()


async def change_member_reputation(
    chat_id: int,
    user_id: int,
    amount: int,
):
    """
    Изменяет репутацию относительно текущего значения.

    Например:

        +5 -> добавить 5
        -10 -> снять 10
    """

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO member_profiles
            (
                chat_id,
                user_id,
                reputation
            )
            VALUES (?, ?, ?)

            ON CONFLICT(chat_id, user_id)
            DO UPDATE SET
                reputation = reputation + ?,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                chat_id,
                user_id,
                0,
                amount,
            ),
        )

        await db.commit()


# ============================================================
# FULL UPDATE
# ============================================================

async def update_member_profile(
    chat_id: int,
    user_id: int,
    display_name: str | None = None,
    role_id: int | None = None,
    rank_id: int | None = None,
    legion_id: int | None = None,
    status_id: int | None = None,
    reputation: int = 0,
):
    """
    Полностью обновляет карточку участника.

    ВАЖНО:
    Эта функция устанавливает все переданные поля.
    Если role_id/rank_id/legion_id/status_id равны None,
    соответствующее поле будет очищено.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO member_profiles
            (
                chat_id,
                user_id,
                display_name,
                role_id,
                rank_id,
                legion_id,
                status_id,
                reputation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(chat_id, user_id)
            DO UPDATE SET
                display_name = excluded.display_name,
                role_id = excluded.role_id,
                rank_id = excluded.rank_id,
                legion_id = excluded.legion_id,
                status_id = excluded.status_id,
                reputation = excluded.reputation,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                chat_id,
                user_id,
                display_name,
                role_id,
                rank_id,
                legion_id,
                status_id,
                reputation,
            ),
        )

        await db.commit()


# ============================================================
# DELETE
# ============================================================

async def delete_member_profile(
    chat_id: int,
    user_id: int,
):
    """
    Удаляет карточку участника.

    Запись в seen_users при этом НЕ удаляется.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            DELETE FROM member_profiles
            WHERE chat_id = ?
              AND user_id = ?
            """,
            (
                chat_id,
                user_id,
            ),
        )

        await db.commit()


# ============================================================
# EXISTENCE
# ============================================================

async def member_profile_exists(
    chat_id: int,
    user_id: int,
) -> bool:
    """
    Проверяет существование карточки участника.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT 1
            FROM member_profiles
            WHERE chat_id = ?
              AND user_id = ?
            LIMIT 1
            """,
            (
                chat_id,
                user_id,
            ),
        )

        row = await cursor.fetchone()

        return row is not None


# ============================================================
# ENSURE PROFILE
# ============================================================

async def ensure_member_profile(
    chat_id: int,
    user_id: int,
    display_name: str | None = None,
):
    """
    Гарантирует наличие карточки участника.

    Если карточка существует - ничего не меняет.
    Если карточки нет - создаёт её.
    """

    await create_member_profile(
        chat_id=chat_id,
        user_id=user_id,
        display_name=display_name,
    )