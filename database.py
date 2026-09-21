import os

import asyncpg
from dotenv import load_dotenv


load_dotenv()


DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


async def create_database():
    connection = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    await connection.execute("""
        CREATE TABLE IF NOT EXISTS linked_accounts (
            discord_id BIGINT PRIMARY KEY,
            riot_id VARCHAR(100) NOT NULL,
            puuid VARCHAR(100) NOT NULL,
            platform VARCHAR(10) NOT NULL
        )
    """)

    await connection.close()


async def save_account(
    discord_id,
    riot_id,
    puuid,
    platform
):
    connection = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    await connection.execute("""
        INSERT INTO linked_accounts (
            discord_id,
            riot_id,
            puuid,
            platform
        )
        VALUES ($1, $2, $3, $4)

        ON CONFLICT (discord_id)
        DO UPDATE SET
            riot_id = EXCLUDED.riot_id,
            puuid = EXCLUDED.puuid,
            platform = EXCLUDED.platform
    """,
        discord_id,
        riot_id,
        puuid,
        platform
    )

    await connection.close()