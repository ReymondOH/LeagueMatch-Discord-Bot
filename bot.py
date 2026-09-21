import os
import asyncio

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from database import (
    delete_account,
    get_announcement_channel,
    set_announcement_channel,
    create_database,
    save_account,
    get_account,
    get_all_accounts,
    get_last_game_id,
    update_last_game_id
)

from riot_api import (
    get_account_by_riot_id,
    get_current_game,
    get_champion_names,
    get_player_rank
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

        guild = bot.get_guild(guild_id)

        if guild is None:
            print(f"{riot_id}: Discord server not found")
            continue

        member = guild.get_member(discord_id)

        if member is None:
            print(f"{riot_id}: Discord member not found in {guild.name}")
            continue
        

        if member is None:
            print(f"{riot_id}: Discord member not found")
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
                platform
            )

            await channel.send(embed=embed)

            await update_last_game_id(guild_id, discord_id, game_id)

            print(f"{riot_id}: Notification sent for game {game_id}")

        else:
            print(f"{riot_id}: Not playing League - skipping")

@check_player_activity.before_loop
async def before_check_player_activity():
    await bot.wait_until_ready()

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