import asyncio
import logging

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError

logger = logging.getLogger(__name__)


async def get_member(bot: Bot, chat_id: int, user_id: int):
    try:
        return await bot.get_chat_member(chat_id, user_id)
    except TelegramAPIError as exc:
        logger.warning(
            "Could not get member user_id=%s chat_id=%s: %s",
            user_id,
            chat_id,
            exc,
        )
        return None


async def is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    member = await get_member(bot, chat_id, user_id)

    return bool(
        member
        and member.status
        in {
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.ADMINISTRATOR,
        }
    )


async def get_admin_ids(bot: Bot, chat_id: int) -> set[int]:
    admins = await bot.get_chat_administrators(chat_id)
    return {admin.user.id for admin in admins}


class AdaptiveThrottle:
    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 8.0,
        increase_factor: float = 1.6,
        recovery_after: int = 10,
    ) -> None:
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.increase_factor = increase_factor
        self.recovery_after = recovery_after
        self.current_delay = base_delay
        self._success_streak = 0

    async def wait(self) -> None:
        await asyncio.sleep(self.current_delay)

    def on_success(self) -> None:
        self._success_streak += 1

        if (
            self._success_streak >= self.recovery_after
            and self.current_delay > self.base_delay
        ):
            self.current_delay = max(
                self.base_delay,
                self.current_delay / self.increase_factor,
            )
            self._success_streak = 0

    def on_flood_wait(self, retry_after: float) -> None:
        self._success_streak = 0
        self.current_delay = min(
            self.max_delay,
            max(
                self.current_delay * self.increase_factor,
                retry_after * 0.1,
            ),
        )
