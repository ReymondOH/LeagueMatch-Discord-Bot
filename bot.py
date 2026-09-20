import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from riot_api import get_account_by_riot_id, get_current_game


load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


RIOT_API_KEY = os.getenv("RIOT_API_KEY")
print("Riot key loaded:", RIOT_API_KEY is not None)


@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)

    print(f"Logged in as {bot.user}")
    print(f"Synced {len(synced)} commands to test server")


@bot.tree.command(
    name="link",
    description="Link your Riot account to Discord"
)
async def link(
    interaction: discord.Interaction,
    game_name: str,
    tag_line: str
):
    await interaction.response.defer()

    account = await get_account_by_riot_id(
        game_name,
        tag_line
    )

    if account is None:
        await interaction.followup.send(
            "Could not find that Riot account."
        )
        return

    puuid = account["puuid"]
    riot_name = account["gameName"]
    riot_tag = account["tagLine"]

    await interaction.followup.send(
        f"Found Riot account: **{riot_name}#{riot_tag}**\n"
        f"PUUID: `{puuid}`"
    )

@bot.tree.command(
    name="live",
    description="Check if a Riot account is currently in a League game"
)
async def live(
    interaction: discord.Interaction,
    game_name: str,
    tag_line: str
):
    await interaction.response.defer()

    account = await get_account_by_riot_id(
        game_name,
        tag_line
    )

    if account is None:
        await interaction.followup.send(
            "Could not find that Riot account."
        )
        return

    puuid = account["puuid"]

    game = await get_current_game(
        puuid,
        platform="la1"
    )

    if game is None:
        await interaction.followup.send(
            f"**{game_name}#{tag_line}** is not currently in a game."
        )
        return

    await interaction.followup.send(
        f"🎮 **{game_name}#{tag_line} is currently in a League game!**"
    )


bot.run(DISCORD_TOKEN)