from aiogram import Router, types, Bot
from aiogram.filters import Command

from database.db import count_seen_users
from database.permissions import can_view_audit_log, can_manage_admins
from mtproto import sync_chat_members

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: types.Message, bot: Bot):
    # VIEW_AUDIT_LOG выбран как ближайшее по смыслу право из существующих —
    # отдельного "view_stats" в database/models.py нет. Соответствует
    # bot_roadmap.md: просмотр статистики закреплён за Senior Admin+.
    if not await can_view_audit_log(bot, message.chat.id, message.from_user.id):
        return await message.reply("Недостаточно Порчи в твоей крови для этого ритуала.")

    tracked_count = await count_seen_users(message.chat.id)

    # Реальное общее число участников чата — берём напрямую из Telegram,
    # т.к. seen_users учитывает только тех, кто писал сообщения или
    # заходил ПОСЛЕ того, как бот начал их отслеживать (Bot API не даёт
    # ботам получить полный список участников группы — ограничение
    # приватности Telegram, не баг бота). Полную синхронизацию списка
    # можно сделать командой /sync (через Telethon-клиент).
    try:
        real_count = await bot.get_chat_member_count(message.chat.id)
    except Exception:
        real_count = None

    lines = []

    if real_count is not None:
        lines.append(f"Всего участников чата (по данным Telegram): <b>{real_count}</b>")

    lines.append(f"Отслежено в базе: <b>{tracked_count}</b>")

    if real_count is not None and real_count > tracked_count:
        lines.append(
            "\n<i>Есть расхождение — выполни /sync, чтобы подтянуть "
            "полный список участников через Telethon.</i>"
        )

    await message.reply("\n".join(lines))


@router.message(Command("sync"))
async def cmd_sync(message: types.Message, bot: Bot):
    # Синхронизация — по сути управление данными администраторов/учёта,
    # поэтому используем то же право, что и для управления админами:
    # доступно owner/superadmin.
    if not await can_manage_admins(bot, message.chat.id, message.from_user.id):
        return await message.reply("Недостаточно Порчи в твоей крови для этого ритуала.")

    status_message = await message.reply("Синхронизация участников через Telethon...")

    try:
        count = await sync_chat_members(message.chat.id)
    except Exception as e:
        return await status_message.edit_text(
            f"Ошибка синхронизации: {e}"
        )

    await status_message.edit_text(
        f"Синхронизация завершена. Обработано участников: <b>{count}</b>"
    )