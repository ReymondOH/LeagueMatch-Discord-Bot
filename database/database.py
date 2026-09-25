import os

import asyncpg
from dotenv import load_dotenv


load_dotenv()


DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

async def get_setup_stats(champion_id):
    """Aggregate ranked solo matches for one champion across all roles."""
    connection = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
        ssl=os.getenv("DB_SSL", "require"),
    )
    try:
        return await connection.fetch("""
            SELECT rank_tier, keystone_id,
                   LEAST(spell1_id, spell2_id) AS spell_low,
                   GREATEST(spell1_id, spell2_id) AS spell_high,
                   COUNT(*)::int AS games,
                   COUNT(*) FILTER (WHERE win)::int AS wins
            FROM match_stats
            WHERE champion_id = $1 AND rank_tier IN
                ('CHALLENGER', 'GRANDMASTER', 'MASTER', 'DIAMOND', 'EMERALD')
            GROUP BY rank_tier, keystone_id, spell_low, spell_high
        """, champion_id)
    finally:
        await connection.close()


async def add_rank_tier_column():
    """Call once before running the rank-aware collector."""
    connection = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
        ssl=os.getenv("DB_SSL", "require"),
    )
    try:
        await connection.execute(
            "ALTER TABLE match_stats ADD COLUMN IF NOT EXISTS rank_tier VARCHAR(20)"
        )
    finally:
        await connection.close()


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
        tracking_enabled BOOLEAN NOT NULL DEFAULT TRUE,
        PRIMARY KEY (guild_id, discord_id)
        )
    """)

    await connection.execute("""
    CREATE TABLE IF NOT EXISTS guild_settings (
        guild_id BIGINT PRIMARY KEY,
        announcement_channel_id BIGINT NOT NULL
    )
    """)

    await connection.execute("""
        CREATE TABLE IF NOT EXISTS match_stats (
            id SERIAL PRIMARY KEY,

            match_id VARCHAR(100) NOT NULL,
            patch VARCHAR(20) NOT NULL,

            champion_id INTEGER NOT NULL,
            opponent_id INTEGER NOT NULL,

            role VARCHAR(20) NOT NULL,

            keystone_id INTEGER NOT NULL,

            spell1_id INTEGER NOT NULL,
            spell2_id INTEGER NOT NULL,

            win BOOLEAN NOT NULL,

            puuid VARCHAR(100) NOT NULL,

            UNIQUE(match_id, champion_id)
        );
    """)

    await connection.execute("ALTER TABLE match_stats ADD COLUMN IF NOT EXISTS puuid VARCHAR(100)")

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
        SELECT guild_id,
            discord_id,
            riot_id, 
            puuid, 
            platform, 
            tracking_enabled
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

async def set_tracking(guild_id, discord_id, enabled):
    connection = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    await connection.execute("""
        UPDATE linked_accounts
        SET tracking_enabled = $1
        WHERE guild_id = $2
        AND discord_id = $3
    """, enabled, guild_id, discord_id)

    await connection.close()

async def delete_account(guild_id, discord_id):
    connection = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    result = await connection.execute("""
        DELETE FROM linked_accounts
        WHERE guild_id = $1
        AND discord_id = $2
    """, guild_id, discord_id)

    await connection.close()

    return result

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

async def create_match_stats_table():

    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS match_stats (
            id SERIAL PRIMARY KEY,

            match_id VARCHAR(100) NOT NULL,
            patch VARCHAR(20) NOT NULL,

            champion_id INTEGER NOT NULL,
            opponent_id INTEGER NOT NULL,

            role VARCHAR(20) NOT NULL,

            keystone_id INTEGER NOT NULL,

            spell1_id INTEGER NOT NULL,
            spell2_id INTEGER NOT NULL,

            win BOOLEAN NOT NULL,

            puuid VARCHAR(100),

            UNIQUE(match_id, champion_id)
        );
    """)

    await conn.execute("ALTER TABLE match_stats ADD COLUMN IF NOT EXISTS puuid VARCHAR(100)")

    await conn.close()

async def save_match_stat(
    match_id,
    patch,
    champion_id,
    opponent_id,
    role,
    keystone_id,
    spell1_id,
    spell2_id,
    win,
    puuid,
    rank_tier=None
):

    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    await conn.execute("""
        INSERT INTO match_stats (
            match_id,
            patch,
            champion_id,
            opponent_id,
            role,
            keystone_id,
            spell1_id,
            spell2_id,
            win,
            puuid,
            rank_tier
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        ON CONFLICT (match_id, champion_id)
        DO UPDATE SET
            puuid = EXCLUDED.puuid,
            rank_tier = COALESCE(EXCLUDED.rank_tier, match_stats.rank_tier)
    """,
        match_id,
        patch,
        champion_id,
        opponent_id,
        role,
        keystone_id,
        spell1_id,
        spell2_id,
        win,
        puuid,
        rank_tier
    )

    await conn.close()

async def get_sample_puuids(limit=5):
    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    rows = await conn.fetch("""
        SELECT DISTINCT puuid
        FROM match_stats
        WHERE puuid IS NOT NULL
        LIMIT $1
    """, limit)

    await conn.close()

    return [row["puuid"] for row in rows]