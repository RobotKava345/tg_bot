from aiogram import Router, types, Bot
from aiogram.filters import Command

from database.db import count_seen_users
from database.permissions import can_view_audit_log

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: types.Message, bot: Bot):
    # VIEW_AUDIT_LOG выбран как ближайшее по смыслу право из существующих —
    # отдельного "view_stats" в database/models.py нет. Соответствует
    # bot_roadmap.md: просмотр статистики закреплён за Senior Admin+.
    if not await can_view_audit_log(bot, message.chat.id, message.from_user.id):
        return await message.reply("Недостаточно Порчи в твоей крови для этого ритуала.")

    count = await count_seen_users(message.chat.id)
    await message.reply(f"В базе по этому чату зафиксировано: <b>{count}</b> пользователей.")