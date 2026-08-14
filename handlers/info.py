from aiogram import Router, types
from aiogram.filters import Command

router = Router()


WELCOME_TEXT = (
    "<b>СЕРВИТОР ХАОСА</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "Машинный дух пробуждён.\n"
    "Я слежу за порядком в этом Чате "
    "по воле тех, кто наделён Порчей власти.\n\n"
    "Флуд и хаос без спроса — не потерпим "
    "(остальной Хаос — сколько угодно).\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Список ритуалов — <code>/commands</code>"
)


COMMANDS_TEXT = (
    "<b>СПИСОК КОМАНД</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Модерация</b> (только для админов)\n"
    "<code>/ban</code> — ответом на сообщение, изгнать в Варп\n"
    "<code>/unban</code> — вернуть душу из Варпа (reply или ID)\n"
    "<code>/mute [минуты]</code> — сковать голос Порчей\n"
    "<code>/unmute</code> — снять Порчу с голоса\n\n"
    "<b>Информация</b>\n"
    "<code>/stats</code> — известно боту участников чата (админы)\n"
    "<code>/commands</code> — этот список\n"
    "━━━━━━━━━━━━━━━━━━━━"
)


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(WELCOME_TEXT)


@router.message(Command("commands"))
async def cmd_commands(message: types.Message):
    await message.answer(COMMANDS_TEXT)