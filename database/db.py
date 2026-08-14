import logging
import aiosqlite

from config import DB_NAME


logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================

async def get_table_columns(
    db: aiosqlite.Connection,
    table_name: str,
) -> set[str]:
    """
    Возвращает список существующих колонок таблицы.
    """

    cursor = await db.execute(
        f"PRAGMA table_info({table_name})"
    )

    rows = await cursor.fetchall()

    return {
        row[1]
        for row in rows
    }


async def add_column_if_missing(
    db: aiosqlite.Connection,
    table_name: str,
    column_name: str,
    column_definition: str,
):
    """
    Добавляет колонку, если её ещё нет.

    SQLite не поддерживает полноценный ALTER TABLE,
    поэтому используем безопасный ADD COLUMN.
    """

    columns = await get_table_columns(
        db,
        table_name,
    )

    if column_name in columns:
        return

    await db.execute(
        f"""
        ALTER TABLE {table_name}
        ADD COLUMN {column_name} {column_definition}
        """
    )

    logger.info(
        "Добавлена колонка %s.%s",
        table_name,
        column_name,
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

async def init_db():
    """
    Инициализирует и при необходимости расширяет SQLite-базу.

    ВАЖНО:

    Эта функция НЕ удаляет существующие таблицы
    и НЕ удаляет существующие данные.

    Она создаёт недостающие таблицы и колонки.
    """

    async with aiosqlite.connect(DB_NAME) as db:

        # ----------------------------------------------------
        # FOREIGN KEYS
        # ----------------------------------------------------

        await db.execute(
            "PRAGMA foreign_keys = ON"
        )

        # ====================================================
        # SEEN USERS
        # ====================================================

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_users (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (chat_id, user_id)
            )
            """
        )

        # ====================================================
        # MEMBER PROFILES
        # ====================================================

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS member_profiles (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                display_name TEXT,

                role_id INTEGER,
                rank_id INTEGER,
                legion_id INTEGER,
                status_id INTEGER,

                reputation INTEGER DEFAULT 0,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (chat_id, user_id)
            )
            """
        )

        # ----------------------------------------------------
        # MIGRATION:
        # старые поля member_profiles
        # ----------------------------------------------------

        member_columns = await get_table_columns(
            db,
            "member_profiles",
        )

        # Старое имя:
        # name -> display_name

        if "display_name" not in member_columns:
            await add_column_if_missing(
                db,
                "member_profiles",
                "display_name",
                "TEXT",
            )

            member_columns = await get_table_columns(
                db,
                "member_profiles",
            )

        if "name" in member_columns:
            await db.execute(
                """
                UPDATE member_profiles
                SET display_name = name
                WHERE display_name IS NULL
                  AND name IS NOT NULL
                """
            )

        # Новые поля карточки

        await add_column_if_missing(
            db,
            "member_profiles",
            "role_id",
            "INTEGER",
        )

        await add_column_if_missing(
            db,
            "member_profiles",
            "rank_id",
            "INTEGER",
        )

        await add_column_if_missing(
            db,
            "member_profiles",
            "legion_id",
            "INTEGER",
        )

        await add_column_if_missing(
            db,
            "member_profiles",
            "status_id",
            "INTEGER",
        )

        await add_column_if_missing(
            db,
            "member_profiles",
            "reputation",
            "INTEGER DEFAULT 0",
        )

        await add_column_if_missing(
            db,
            "member_profiles",
            "created_at",
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        )

        await add_column_if_missing(
            db,
            "member_profiles",
            "updated_at",
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        )

        # ====================================================
        # ROLES
        # ====================================================

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                chat_id INTEGER NOT NULL,

                name TEXT NOT NULL,
                description TEXT,

                active INTEGER NOT NULL DEFAULT 1,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(chat_id, name)
            )
            """
        )

        # ====================================================
        # LEGIONS
        # ====================================================

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS legions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                chat_id INTEGER NOT NULL,

                name TEXT NOT NULL,

                primarch_id INTEGER,

                description TEXT,

                active INTEGER NOT NULL DEFAULT 1,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ----------------------------------------------------
        # MIGRATION LEGIONS
        # ----------------------------------------------------

        await add_column_if_missing(
            db,
            "legions",
            "chat_id",
            "INTEGER",
        )

        await add_column_if_missing(
            db,
            "legions",
            "primarch_id",
            "INTEGER",
        )

        await add_column_if_missing(
            db,
            "legions",
            "active",
            "INTEGER NOT NULL DEFAULT 1",
        )

        await add_column_if_missing(
            db,
            "legions",
            "updated_at",
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        )

        # Старое название:
        # primarch_user_id -> primarch_id

        legion_columns = await get_table_columns(
            db,
            "legions",
        )

        if "primarch_user_id" in legion_columns:
            await db.execute(
                """
                UPDATE legions
                SET primarch_id = primarch_user_id
                WHERE primarch_id IS NULL
                  AND primarch_user_id IS NOT NULL
                """
            )

        # ====================================================
        # RANKS
        # ====================================================

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS ranks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                legion_id INTEGER NOT NULL,

                name TEXT NOT NULL,
                description TEXT,

                points_required INTEGER DEFAULT 0,

                position INTEGER DEFAULT 0,

                active INTEGER NOT NULL DEFAULT 1,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (legion_id)
                    REFERENCES legions(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ----------------------------------------------------
        # MIGRATION RANKS
        # ----------------------------------------------------

        await add_column_if_missing(
            db,
            "ranks",
            "position",
            "INTEGER DEFAULT 0",
        )

        await add_column_if_missing(
            db,
            "ranks",
            "active",
            "INTEGER NOT NULL DEFAULT 1",
        )

        await add_column_if_missing(
            db,
            "ranks",
            "updated_at",
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        )

        # ====================================================
        # STATUSES
        # ====================================================

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS statuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                chat_id INTEGER NOT NULL,

                name TEXT NOT NULL,
                description TEXT,

                active INTEGER NOT NULL DEFAULT 1,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(chat_id, name)
            )
            """
        )

        # ====================================================
        # LEGACY MEMBER STATUSES
        # ====================================================
        #
        # Старую таблицу НЕ удаляем.
        #
        # Она уже существовала в предыдущей архитектуре.
        # Оставляем её для совместимости с текущей БД.
        #
        # Новый код работает с таблицей statuses.
        # ====================================================

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS member_statuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL UNIQUE,

                description TEXT,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # ADMIN TYPES
        # ====================================================

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL UNIQUE,

                description TEXT,

                active INTEGER NOT NULL DEFAULT 1,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # CHAT ADMINS
        # ====================================================

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_admins (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                admin_type_id INTEGER NOT NULL,

                active INTEGER NOT NULL DEFAULT 1,

                assigned_by INTEGER,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (chat_id, user_id),

                FOREIGN KEY (admin_type_id)
                    REFERENCES admin_types(id)
                    ON DELETE RESTRICT
            )
            """
        )

        # ----------------------------------------------------
        # MIGRATION CHAT ADMINS
        # ----------------------------------------------------

        await add_column_if_missing(
            db,
            "chat_admins",
            "active",
            "INTEGER NOT NULL DEFAULT 1",
        )

        await add_column_if_missing(
            db,
            "chat_admins",
            "assigned_by",
            "INTEGER",
        )

        # ====================================================
        # PERMISSIONS
        # ====================================================

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                code TEXT NOT NULL UNIQUE,

                name TEXT NOT NULL,

                description TEXT,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # ADMIN TYPE PERMISSIONS
        # ====================================================

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_type_permissions (
                admin_type_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,

                PRIMARY KEY (
                    admin_type_id,
                    permission_id
                ),

                FOREIGN KEY (admin_type_id)
                    REFERENCES admin_types(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (permission_id)
                    REFERENCES permissions(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ====================================================
        # AUDIT LOG
        # ====================================================

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                chat_id INTEGER NOT NULL,

                actor_id INTEGER NOT NULL,

                action TEXT NOT NULL,

                target_id INTEGER,

                old_value TEXT,

                new_value TEXT,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # INDEXES
        # ====================================================

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_seen_users_chat
            ON seen_users(chat_id)
            """
        )

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_member_profiles_chat
            ON member_profiles(chat_id)
            """
        )

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_member_profiles_user
            ON member_profiles(user_id)
            """
        )

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_roles_chat
            ON roles(chat_id)
            """
        )

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_legions_chat
            ON legions(chat_id)
            """
        )

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_ranks_legion
            ON ranks(legion_id)
            """
        )

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_statuses_chat
            ON statuses(chat_id)
            """
        )

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_chat_admins_chat
            ON chat_admins(chat_id)
            """
        )

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_audit_logs_chat
            ON audit_logs(chat_id)
            """
        )

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_audit_logs_actor
            ON audit_logs(actor_id)
            """
        )

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_audit_logs_target
            ON audit_logs(target_id)
            """
        )

        # ====================================================
        # COMMIT
        # ====================================================

        await db.commit()

    logger.info(
        "Структура базы данных инициализирована"
    )


# ============================================================
# SEEN USERS
# ============================================================

async def add_user(
    chat_id: int,
    user_id: int,
):
    """
    Добавляет пользователя в реестр замеченных пользователей.

    Старый функционал сохранён.
    """

    try:

        async with aiosqlite.connect(DB_NAME) as db:

            await db.execute(
                """
                INSERT OR IGNORE INTO seen_users
                (
                    chat_id,
                    user_id
                )
                VALUES (?, ?)
                """,
                (
                    chat_id,
                    user_id,
                ),
            )

            await db.commit()

    except Exception as e:

        logger.error(
            "Ошибка записи пользователя %s "
            "в чат %s: %s",
            user_id,
            chat_id,
            e,
        )


async def get_seen_users(
    chat_id: int,
) -> list[int]:
    """
    Возвращает ID всех пользователей,
    когда-либо замеченных в чате.
    """

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            """
            SELECT user_id
            FROM seen_users
            WHERE chat_id = ?
            """,
            (
                chat_id,
            ),
        )

        rows = await cursor.fetchall()

        return [
            row[0]
            for row in rows
        ]


async def count_seen_users(
    chat_id: int,
) -> int:
    """
    Возвращает количество замеченных пользователей.
    """

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM seen_users
            WHERE chat_id = ?
            """,
            (
                chat_id,
            ),
        )

        row = await cursor.fetchone()

        return row[0] if row else 0