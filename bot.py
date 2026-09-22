import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from services.match_tracker import setup_match_tracker
from database.database import (
    set_tracking,
    delete_account,
    set_announcement_channel,
    create_database,
    save_account,
    get_account,
)

from utils.embeds import create_match_embed

from services.riot_api import (
    get_account_by_riot_id,
    get_current_game,
)


load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.presences = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)



RIOT_API_KEY = os.getenv("RIOT_API_KEY")
print("Riot key loaded:", RIOT_API_KEY is not None)



@bot.event
async def on_ready():
    await create_database()

    #Sync global commands
    synced = await bot.tree.sync()

    if not check_player_activity.is_running():
        check_player_activity.start()

    print(f"Logged in as {bot.user}")
    print(f"Connected to PostgreSQL")
    print(f"Synced {len(synced)} commands")



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

    riot_id = f"{riot_name}#{riot_tag}"

    await save_account(
        interaction.guild.id,
        interaction.user.id,
        riot_id,
        puuid,
        "la1"
    )

    await interaction.followup.send(
        f"✅ **{riot_id}** has been linked to "
        f"{interaction.user.mention}."
    )

@bot.tree.command(
    name="unlink",
    description="Unlink your Riot account from this Discord server"
)
async def unlink(interaction: discord.Interaction):

    if interaction.guild is None:
        await interaction.response.send_message(
            "This command can only be used inside a server."
        )
        return

    account = await get_account(
        interaction.guild.id,
        interaction.user.id
    )

    if account is None:
        await interaction.response.send_message(
            "You do not have a Riot account linked in this server."
        )
        return

    riot_id = account["riot_id"]

    await delete_account(
        interaction.guild.id,
        interaction.user.id
    )

    await interaction.response.send_message(
        f"✅ **{riot_id}** has been unlinked from your Discord account."
    )

@bot.tree.command(
    name="tracking",
    description="Enable or disable automatic League match notifications"
)
async def tracking(
    interaction: discord.Interaction,
    enabled: bool
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command can only be used inside a server.",
            ephemeral=True
        )
        return

    account = await get_account(
        interaction.guild.id,
        interaction.user.id
    )

    if account is None:
        await interaction.response.send_message(
            "You have not linked a Riot account yet. Use `/link` first.",
            ephemeral=True
        )
        return

    await set_tracking(
        interaction.guild.id,
        interaction.user.id,
        enabled
    )

    if enabled:
        await interaction.response.send_message(
            "✅ Automatic match notifications are now enabled."
        )
    else:
        await interaction.response.send_message(
            "🔕 Automatic match notifications are now disabled."
        )

check_player_activity = setup_match_tracker(
    bot,
    create_match_embed
)


#Temporary command to check if the bot can read the user's Discord activity
@bot.tree.command(
    name="activity",
    description="Check your current Discord activity"
)
async def activity(interaction: discord.Interaction):

    member = interaction.user

    print(f"Checking activity for {member}")

    for activity in member.activities:
        print(activity.name)

    playing_league = any(
        activity.name == "League of Legends"
        for activity in member.activities
    )

    if playing_league:
        await interaction.response.send_message(
            "League of Legends detected!"
        )
    else:
        await interaction.response.send_message(
            "League of Legends not detected."
        )


@bot.tree.command(
    name="setchannel",
    description="Set the channel for League match notifications"
)
async def setchannel(
    interaction: discord.Interaction,
    channel: discord.TextChannel
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command can only be used inside a server.",
            ephemeral=True
        )
        return

    if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "You need the Manage Server permission to use this command.",
                ephemeral=True
            )
            return

    await set_announcement_channel(
        interaction.guild.id,
        channel.id
    )

    await interaction.response.send_message(
        f"League match notifications will be sent to {channel.mention}."
    )


@bot.tree.command(
    name="live",
    description="Check if your linked Riot account is currently in a League game"
)
async def live(
    interaction: discord.Interaction
):
    await interaction.response.defer()

    if interaction.guild is None:
        await interaction.followup.send(
            "This command can only be used inside a server."
        )
        return

    account = await get_account(interaction.guild.id, interaction.user.id)

    if account is None:
        await interaction.followup.send(
            "You have not linked your Riot account yet. "
            "Use the `/link` command to link your account."
        )
        return

    riot_id = account["riot_id"]
    puuid = account["puuid"]
    platform = account["platform"]

    game = await get_current_game(
        puuid,
        platform=platform
    )

    if game is None:
        await interaction.followup.send(
            f"**{riot_id}** is not currently in a game."
        )
        return

    embed = await create_match_embed(
        game,
        riot_id,
        platform
    )

    await interaction.followup.send(embed=embed)

bot.run(DISCORD_TOKEN)