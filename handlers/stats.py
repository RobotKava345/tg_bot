from aiogram import Router, types, Bot
from aiogram.filters import Command

from utils import is_admin
from database.db import count_seen_users

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: types.Message, bot: Bot):
    if not await is_admin(bot, message.chat.id, message.from_user.id):
        return await message.reply("Недостаточно прав.")

    count = await count_seen_users(message.chat.id)
    await message.reply(f"В базе по этому чату зафиксировано: <b>{count}</b> пользователей.")