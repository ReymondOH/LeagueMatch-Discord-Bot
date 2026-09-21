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
        guild_id BIGINT NOT NULL,
        discord_id BIGINT NOT NULL,
        riot_id VARCHAR(100) NOT NULL,
        puuid VARCHAR(100) NOT NULL,
        platform VARCHAR(10) NOT NULL,
        last_game_id BIGINT,
        PRIMARY KEY (guild_id, discord_id)
        )
    """)

    await connection.execute("""
    CREATE TABLE IF NOT EXISTS guild_settings (
        guild_id BIGINT PRIMARY KEY,
        announcement_channel_id BIGINT NOT NULL
    )
""")

    await connection.close()


async def save_account(
    guild_id,
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
            guild_id,
            discord_id,
            riot_id,
            puuid,
            platform
        )
        VALUES ($1, $2, $3, $4, $5)

        ON CONFLICT (guild_id,discord_id)
        DO UPDATE SET
            riot_id = EXCLUDED.riot_id,
            puuid = EXCLUDED.puuid,
            platform = EXCLUDED.platform
    """,
        guild_id,
        discord_id,
        riot_id,
        puuid,
        platform
    )

    await connection.close()

async def get_account(guild_id, discord_id):
    connection = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    account = await connection.fetchrow("""
        SELECT riot_id, puuid, platform
        FROM linked_accounts
        WHERE guild_id = $1 AND discord_id = $2
    """, guild_id, discord_id)

    await connection.close()

    return account

async def get_all_accounts():
    connection = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    accounts = await connection.fetch("""
        SELECT guild_id,discord_id, riot_id, puuid, platform
        FROM linked_accounts
    """)

    await connection.close()

    return accounts

async def get_last_game_id(guild_id, discord_id):
    connection = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    last_game_id = await connection.fetchval("""
        SELECT last_game_id
        FROM linked_accounts
        WHERE guild_id = $1 AND discord_id = $2
    """, guild_id, discord_id)

    await connection.close()

    return last_game_id

async def update_last_game_id(guild_id, discord_id, game_id):
    connection = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    await connection.execute("""
        UPDATE linked_accounts
        SET last_game_id = $1
        WHERE guild_id = $2 AND discord_id = $3
    """, game_id, guild_id, discord_id)

    await connection.close()

async def set_announcement_channel(guild_id, channel_id):
    connection = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    await connection.execute("""
        INSERT INTO guild_settings (
            guild_id,
            announcement_channel_id
        )
        VALUES ($1, $2)

        ON CONFLICT (guild_id)
        DO UPDATE SET
            announcement_channel_id = EXCLUDED.announcement_channel_id
    """, guild_id, channel_id)

    await connection.close()


async def get_announcement_channel(guild_id):
    connection = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    channel_id = await connection.fetchval("""
        SELECT announcement_channel_id
        FROM guild_settings
        WHERE guild_id = $1
    """, guild_id)

    await connection.close()

    return channel_id