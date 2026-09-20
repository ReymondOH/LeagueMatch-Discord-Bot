import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from riot_api import get_account_by_riot_id


load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


RIOT_API_KEY = os.getenv("RIOT_API_KEY")
print("Riot key loaded:", RIOT_API_KEY is not None)


@bot.event
async def on_ready():
    await bot.tree.sync()

    print(f"Logged in as {bot.user}")
    print("Slash commands synced!")


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


bot.run(DISCORD_TOKEN)