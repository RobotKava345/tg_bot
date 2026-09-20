from aiogram import Router, types
from aiogram.filters import Command

router = Router()

WELCOME_TEXT = (
    "<b>Telegram Admin Bot Template</b>\n\n"
    "Bot is running. Use <code>/commands</code> to see available commands."
)

COMMANDS_TEXT = (
    "<b>Commands</b>\n\n"
    "<code>/start</code> — check that the bot is alive\n"
    "<code>/commands</code> — show this list\n"
    "<code>/stats</code> — show Telegram and tracked member counts\n"
    "<code>/sync</code> — synchronize members through Telethon\n"
    "<code>/fire_exterminatus confirm</code> — optional destructive cleanup; "
    "disabled by default and restricted to Telegram admins"
)


@router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    await message.answer(WELCOME_TEXT)


@router.message(Command("commands"))
async def cmd_commands(message: types.Message) -> None:
    await message.answer(COMMANDS_TEXT)
