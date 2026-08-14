import logging

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
)

from telethon import functions, types

from mtproto import client


logger = logging.getLogger(__name__)

# Telegram General topic
GENERAL_TOPIC_ID = 1


async def find_chat(chat_id: int):
    """
    Находит чат через уже авторизованный Telethon-клиент.

    Используется существующая Telethon-сессия из mtproto.py.
    Новый TelegramClient здесь не создаётся.
    """

    async for dialog in client.iter_dialogs():
        if dialog.id == chat_id:
            logger.info(
                "Telethon нашёл чат '%s' (%s)",
                dialog.name,
                chat_id,
            )

            return dialog.entity

    raise ValueError(
        f"Чат {chat_id} не найден среди диалогов Telethon"
    )


async def get_forum_topics(chat_id: int):
    """
    Получает список форумных веток через MTProto.
    """

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

    topics = [
        topic
        for topic in result.topics
        if isinstance(topic, types.ForumTopic)
    ]

    logger.info(
        "Получено форумных веток для '%s': %d",
        chat_id,
        len(topics),
    )

    return topics


async def get_topic_info(chat_id: int):
    """
    Возвращает информацию о форумных ветках.
    """

    topics = await get_forum_topics(chat_id)

    return [
        {
            "id": topic.id,
            "title": topic.title,
            "closed": topic.closed,
            "hidden": topic.hidden,
        }
        for topic in topics
    ]


async def delete_all_topics_except(
    bot: Bot,
    chat_id: int,
    keep_topic_id: int | None = None,
):
    """
    Удаляет все форумные ветки, кроме указанной.

    General (ID=1) всегда сохраняется.

    keep_topic_id:
        ID ветки, из которой была выполнена команда /ext.

    Возвращает:

        total_topics
        deleted
        errors
    """

    topics = await get_forum_topics(chat_id)

    total_topics = len(topics)
    deleted = 0
    errors = 0

    logger.info(
        "Начинается очистка форума '%s'. Найдено веток: %d",
        chat_id,
        total_topics,
    )

    for topic in topics:
        topic_id = topic.id
        topic_title = topic.title

        # ==========================================================
        # GENERAL
        # ==========================================================

        if topic_id == GENERAL_TOPIC_ID:
            logger.info(
                "General сохранён: ID=%s",
                topic_id,
            )
            continue

        # ==========================================================
        # ТЕКУЩАЯ ВЕТКА
        # ==========================================================

        if (
            keep_topic_id is not None
            and topic_id == keep_topic_id
        ):
            logger.info(
                "Текущая ветка сохранена: '%s' (ID=%s)",
                topic_title,
                topic_id,
            )
            continue

        # ==========================================================
        # УДАЛЕНИЕ
        # ==========================================================

        try:
            await bot.delete_forum_topic(
                chat_id=chat_id,
                message_thread_id=topic_id,
            )

            deleted += 1

            logger.info(
                "Ветка удалена: '%s' (ID=%s)",
                topic_title,
                topic_id,
            )

        except TelegramForbiddenError as e:
            errors += 1

            logger.error(
                "Недостаточно прав для удаления "
                "'%s' (ID=%s): %s",
                topic_title,
                topic_id,
                e,
            )

        except TelegramBadRequest as e:
            errors += 1

            logger.error(
                "Telegram отклонил удаление "
                "'%s' (ID=%s): %s",
                topic_title,
                topic_id,
                e,
            )

        except Exception as e:
            errors += 1

            logger.exception(
                "Ошибка удаления "
                "'%s' (ID=%s): %s",
                topic_title,
                topic_id,
                e,
            )

    logger.info(
        "Очистка форума завершена: "
        "найдено=%d, удалено=%d, ошибок=%d",
        total_topics,
        deleted,
        errors,
    )

    return total_topics, deleted, errors