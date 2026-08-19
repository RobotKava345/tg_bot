import asyncio
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

# ============================================================
# ПАРАМЕТРЫ ЗАМЕНЯЮЩЕЙ ВЕТКИ "АВЕ ИМП"
# ============================================================

REPLACEMENT_TOPIC_NAME = "АВЕ ИМП"

REPLACEMENT_TOPIC_TEXT = (
    "<b>Заявление об ответственности за операцию «Альфа Легион»</b>\n\n"
    "<i>«Тень не просит прощения за то, что делает свою работу.»</i>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Специальное подразделение внешней разведки «Альфа Легион» "
    "Империума Человечества берёт на себя полную ответственность "
    "за выполнение данной операции, направленной на уничтожение "
    "Хаоса как сообщества.\n\n"
    "Ответственность лежит на этих людях:\n\n"
    "@Nnigghha — автор плана всей операции\n"
    "@Nnigghha — реализатор всей фиктивной инфраструктуры под операцию\n"
    "@Nnigghha — реализатор внедрения в Хаос\n"
    "@Nnigghha — реализатор социально-технической части всей операции, "
    "включая написание бота\n"
    "@IlonelIy — санкционировал операцию\n"
    "Рубик — помогал с организацией операции\n"
    "@archivist444 — помогал с организацией операции\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Империум выражает большую благодарность Арчу (@Artemka_218) "
    "за непрепятствование и даже лоббирование наших агентов "
    "во время исполнения данной операции.\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Слава Империуму Человечества.</b>"
)


async def create_replacement_topic(
    bot: Bot,
    chat_id: int,
):
    """
    Создаёт новую форумную ветку "АВЕ ИМП" на месте удалённой
    и публикует в ней заявление об ответственности.

    Возвращает True при успехе, False при ошибке.
    """

    try:
        new_topic = await bot.create_forum_topic(
            chat_id=chat_id,
            name=REPLACEMENT_TOPIC_NAME,
        )

        await bot.send_message(
            chat_id=chat_id,
            message_thread_id=new_topic.message_thread_id,
            text=REPLACEMENT_TOPIC_TEXT,
        )

        logger.info(
            "Создана заменяющая ветка '%s' (ID=%s) в чате %s",
            REPLACEMENT_TOPIC_NAME,
            new_topic.message_thread_id,
            chat_id,
        )

        return True

    except Exception as e:
        logger.exception(
            "Не удалось создать заменяющую ветку в чате %s: %s",
            chat_id,
            e,
        )

        return False


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
    created = 0

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

            # ==========================================================
            # СОЗДАНИЕ ЗАМЕНЯЮЩЕЙ ВЕТКИ "АВЕ ИМП"
            # ==========================================================

            if await create_replacement_topic(bot=bot, chat_id=chat_id):
                created += 1

            # Небольшая пауза, чтобы не спровоцировать flood-control
            # при удалении+создании множества веток подряд.
            await asyncio.sleep(0.5)

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
        "найдено=%d, удалено=%d, создано=%d, ошибок=%d",
        total_topics,
        deleted,
        created,
        errors,
    )

    return total_topics, deleted, created, errors