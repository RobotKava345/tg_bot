import asyncio

from forum_topics import get_topic_info
from mtproto import client


CHAT_ID = -1003993853383


async def main():
    await client.start()

    topics = await get_topic_info(CHAT_ID)

    print()
    print("=== ВЕТКИ ХАОСИТОВ ===")

    for topic in topics:
        print(
            f"ID={topic['id']} | "
            f"title={topic['title']} | "
            f"closed={topic['closed']} | "
            f"hidden={topic['hidden']}"
        )

    print("======================")
    print(f"Всего веток: {len(topics)}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())