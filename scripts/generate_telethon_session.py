"""
Generate a Telethon StringSession for local development or deployment.

Never commit the resulting string to Git.
Put it in .env locally or in the hosting provider's secret environment variables.
"""

import os

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()


async def main() -> None:
    api_id_raw = os.getenv("TELEGRAM_API_ID", "").strip()
    api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()

    if not api_id_raw or not api_hash:
        raise RuntimeError(
            "Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env first."
        )

    api_id = int(api_id_raw)

    async with TelegramClient(StringSession(), api_id, api_hash) as client:
        print("\nTELETHON_SESSION_STRING=")
        print(client.session.save())
        print(
            "\nStore this value as a secret. Anyone who has it may be able "
            "to access the authorized Telegram account."
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
