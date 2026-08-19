"""
Разовый скрипт: назначает указанного пользователя владельцем (owner)
в конкретном чате напрямую через asyncpg, в обход мини-аппа и бота.

Запуск:
    pip install asyncpg          # если ещё не стоит
    python make_me_owner.py

Перед запуском заполни три переменные ниже.
"""

import asyncio
import asyncpg


# ============================================================
# ЗАПОЛНИ ЭТИ ЗНАЧЕНИЯ
# ============================================================

DATABASE_URL = "postgresql://admcore_db_user:34nErXo5pXVvLzxDo1uJ71BDyltI2LkT@dpg-da0e02jl550s73d7tiqg-a.frankfurt-postgres.render.com/admcore_db"

CHAT_ID = -1002427719174   # клан Хаос
USER_ID = 1681093322


# ============================================================
# ВСЕ ПРАВА, КОТОРЫЕ ДОЛЖНЫ БЫТЬ У OWNER
# ============================================================

ALL_PERMISSIONS = [
    ("view_profile", "View profile"),
    ("edit_name", "Edit name"),
    ("edit_role", "Edit role"),
    ("edit_rank", "Edit rank"),
    ("edit_legion", "Edit legion"),
    ("edit_status", "Edit status"),
    ("edit_reputation", "Edit reputation"),
    ("manage_ranks", "Manage ranks"),
    ("manage_legions", "Manage legions"),
    ("manage_roles", "Manage roles"),
    ("manage_statuses", "Manage statuses"),
    ("manage_admins", "Manage admins"),
    ("manage_permissions", "Manage permissions"),
    ("moderate_users", "Moderate users"),
    ("view_audit_log", "View audit log"),
]


async def main():
    if CHAT_ID == 0 or USER_ID == 0:
        print("ОШИБКА: заполни CHAT_ID и USER_ID в начале файла.")
        return

    conn = await asyncpg.connect(dsn=DATABASE_URL)

    try:
        # 1) admin_types: убедиться, что owner есть
        await conn.execute(
            """
            INSERT INTO admin_types (name, description)
            VALUES ('owner', 'Полный доступ ко всем функциям бота.')
            ON CONFLICT (name) DO NOTHING
            """
        )

        owner_id = await conn.fetchval(
            "SELECT id FROM admin_types WHERE name = 'owner'"
        )

        # 2) permissions: досеять все коды, если их нет
        for code, name in ALL_PERMISSIONS:
            await conn.execute(
                """
                INSERT INTO permissions (code, name)
                VALUES ($1, $2)
                ON CONFLICT (code) DO NOTHING
                """,
                code, name,
            )

        # 3) admin_type_permissions: owner получает все права
        rows_added = 0
        for code, _ in ALL_PERMISSIONS:
            permission_id = await conn.fetchval(
                "SELECT id FROM permissions WHERE code = $1", code
            )
            status = await conn.execute(
                """
                INSERT INTO admin_type_permissions (admin_type_id, permission_id)
                VALUES ($1, $2)
                ON CONFLICT (admin_type_id, permission_id) DO NOTHING
                """,
                owner_id, permission_id,
            )
            if status.endswith(" 1"):
                rows_added += 1

        # 4) chat_admins: назначить тебя owner в этом чате
        await conn.execute(
            """
            INSERT INTO chat_admins (chat_id, user_id, admin_type_id, active, assigned_by)
            VALUES ($1, $2, $3, TRUE, $2)
            ON CONFLICT (chat_id, user_id) DO UPDATE SET
                admin_type_id = EXCLUDED.admin_type_id,
                active = TRUE
            """,
            CHAT_ID, USER_ID, owner_id,
        )

        print(f"Готово. owner_id={owner_id}, добавлено новых прав: {rows_added}")
        print(f"Пользователь {USER_ID} назначен owner в чате {CHAT_ID}.")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())