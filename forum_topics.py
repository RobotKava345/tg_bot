import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from telethon import functions, types

from mtproto import client
from utils import AdaptiveThrottle

logger = logging.getLogger(__name__)

GENERAL_TOPIC_ID = 1


async def find_chat(chat_id: int):
    return await client.get_entity(chat_id)


async def get_forum_topics(chat_id: int):
    chat = await find_chat(chat_id)

    result = await client(
        functions.messages.GetForumTopicsRequest(
            peer=chat,
            q="",
            offset_date=0,
            offset_id=0,
            offset_topic=0,
            limit=100,
        )
    )

    return [
        topic
        for topic in result.topics
        if isinstance(topic, types.ForumTopic)
    ]


async def delete_all_topics_except(
    bot: Bot,
    chat_id: int,
    keep_topic_id: int | None = None,
) -> tuple[int, int, int]:
    topics = await get_forum_topics(chat_id)
    deleted = 0
    errors = 0
    throttle = AdaptiveThrottle()

    for topic in topics:
        if topic.id == GENERAL_TOPIC_ID:
            continue

        if keep_topic_id is not None and topic.id == keep_topic_id:
            continue

        attempts = 0

        while attempts < 2:
            try:
                await bot.delete_forum_topic(
                    chat_id=chat_id,
                    message_thread_id=topic.id,
                )
                deleted += 1
                throttle.on_success()
                break

            except TelegramRetryAfter as exc:
                attempts += 1
                throttle.on_flood_wait(exc.retry_after)
                await asyncio.sleep(exc.retry_after)

            except (TelegramForbiddenError, TelegramBadRequest):
                errors += 1
                logger.exception(
                    "Could not delete topic %s in chat %s",
                    topic.id,
                    chat_id,
                )
                break

        else:
            errors += 1

        await throttle.wait()

    return len(topics), deleted, errors
