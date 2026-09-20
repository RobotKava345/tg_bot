import asyncio
import asyncpg
from config import DATABASE_URL


async def main():
    print("Connecting to PostgreSQL...")

    conn = await asyncpg.connect(
        DATABASE_URL,
        ssl=False,
        timeout=15,
    )

    print("Connected successfully!")

    version = await conn.fetchval("SELECT version()")
    print(version)

    await conn.close()


asyncio.run(main())