import asyncio
import discord

from services.riot_api import (
    get_champion_names,
    get_player_rank
)


async def create_match_embed(game, riot_id, platform):
    champion_names = await get_champion_names()

    blue_team = []
    red_team = []

    rank_tasks = []

    for participant in game["participants"]:
        rank_tasks.append(
            get_player_rank(
                participant["puuid"],
                platform=platform
            )
        )

    player_ranks = await asyncio.gather(*rank_tasks)

    for participant, player_rank in zip(
        game["participants"],
        player_ranks
    ):
        player_riot_id = participant["riotId"]
        champion_id = participant["championId"]

        champion_name = champion_names.get(
            champion_id,
            f"Champion {champion_id}"
        )

        player_info = (
            f"**{player_riot_id}** — {champion_name}\n"
            f"└ {player_rank}"
        )

        if participant["teamId"] == 100:
            blue_team.append(player_info)

        elif participant["teamId"] == 200:
            red_team.append(player_info)

    embed = discord.Embed(
        title="🎮 Live League Match",
        description=f"**{riot_id}** has entered a game!"
    )

    embed.add_field(
        name="🔵 Blue Team",
        value="\n".join(blue_team),
        inline=False
    )

    embed.add_field(
        name="🔴 Red Team",
        value="\n".join(red_team),
        inline=False
    )

    embed.set_footer(
        text=f"Game ID: {game['gameId']}"
    )

    return embed