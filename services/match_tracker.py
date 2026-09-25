import discord
from discord.ext import tasks

from database.database import (
    get_all_accounts,
    get_last_game_id,
    get_announcement_channel,
    update_last_game_id,
)

from services.riot_api import get_current_game

def setup_match_tracker(bot, create_match_embed):


    @tasks.loop(seconds=60)
    async def check_player_activity():
        print("Checking linked player activity...")

        accounts = await get_all_accounts()

        for account in accounts:
            guild_id = account["guild_id"]
            discord_id = account["discord_id"]
            riot_id = account["riot_id"]
            puuid = account["puuid"]
            platform = account["platform"]
            tracking_enabled = account["tracking_enabled"]

            if not tracking_enabled:
                print(f"{riot_id}: Tracking is disabled")
                continue

            guild = bot.get_guild(guild_id)

            if guild is None:
                print(f"{riot_id}: Discord server not found")
                continue

            member = guild.get_member(discord_id)

            if member is None:
                print(f"{riot_id}: Discord member not found in {guild.name}")
                continue

            print(f"Discord member found: {member}")

            print("Activities:")
            for activity in member.activities:
                print(f"  - {activity.name}")

            playing_league = any(
                activity.name == "League of Legends"
                for activity in member.activities
            )

            if playing_league:
                print(f"{riot_id}: Playing League - checking current game")

                game = await get_current_game(
                    puuid,
                    platform=platform
                )

                if game is None:
                    print(f"{riot_id}: Not currently in a game")
                    continue

                game_id = game["gameId"]

                last_game_id = await get_last_game_id(guild_id, discord_id)

                if last_game_id == game_id:
                    print(f"{riot_id}: Already notified for this game - skipping")
                    continue

                print(f"{riot_id}: New game detected"
                    )

                channel_id = await get_announcement_channel(
                    guild_id
                )

                if channel_id is None:
                    print(f"{guild.name}: No annuncement channel set")
                    continue

                channel = bot.get_channel(channel_id)

                if channel is None:
                    print(f"{guild.name}: Announcement channel not found")
                    continue

                embed = await create_match_embed(
                    game, 
                    riot_id,
                    platform,
                    puuid
                )

                await channel.send(embed=embed)

                await update_last_game_id(guild_id, discord_id, game_id)

                print(f"{riot_id}: Notification sent for game {game_id}")

            else:
                print(f"{riot_id}: Not playing League - skipping")

    @check_player_activity.before_loop
    async def before_check_player_activity():
        await bot.wait_until_ready()

    return check_player_activity