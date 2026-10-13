"""Persistent match reminders and private Discord editing controls."""
import json
import logging
import os

import discord
import asyncpg

from database import database as db
from services.riot_api import get_champion_names
from utils.embeds import assign_roles

log = logging.getLogger(__name__)


async def connect():
    return await asyncpg.connect(host=db.DB_HOST, port=db.DB_PORT,
        database=db.DB_NAME, user=db.DB_USER, password=db.DB_PASSWORD,
        ssl=os.getenv('DB_SSL', 'require'))


async def initialize_reminders():
    conn = await connect()
    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS match_reminder_contexts (
                message_id BIGINT PRIMARY KEY, guild_id BIGINT NOT NULL,
                owner_id BIGINT NOT NULL, platform TEXT NOT NULL,
                game_id BIGINT NOT NULL, players JSONB NOT NULL,
                opponent TEXT
            );
            CREATE TABLE IF NOT EXISTS player_reminders (
                guild_id BIGINT NOT NULL, owner_id BIGINT NOT NULL,
                platform TEXT NOT NULL, puuid TEXT NOT NULL,
                riot_id TEXT NOT NULL, note TEXT NOT NULL,
                source_game_id BIGINT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (guild_id, owner_id, platform, puuid)
            );
        ''')
    finally:
        await conn.close()


async def make_context(game, guild_id, owner_id, platform, puuid):
    names = await get_champion_names()
    teams = {}
    players = []
    own = next((p for p in game.get('participants', []) if p.get('puuid') == puuid), None)
    for p in game.get('participants', []):
        champion = names.get(p.get('championId'), f"Champion {p.get('championId')}")
        teams.setdefault(p.get('teamId'), []).append((p, champion, None, None))
        if p.get('puuid') and p['puuid'] != puuid:
            players.append({'puuid': p['puuid'], 'riot_id': p.get('riotId') or
                p.get('summonerName') or 'Nickname unavailable', 'champion': champion,
                'team': 'Ally' if own and p.get('teamId') == own.get('teamId') else 'Enemy'})
    opponent = None
    if own:
        roles, _ = assign_roles(teams.get(own.get('teamId'), []))
        role = next((r for r, player in roles.items() if player[0] is own), None)
        other_roles, _ = assign_roles(teams.get(200 if own.get('teamId') == 100 else 100, []))
        if role in other_roles:
            opponent = other_roles[role][0].get('puuid')
    return {'guild_id': guild_id, 'owner_id': owner_id, 'platform': platform,
            'game_id': game['gameId'], 'players': players, 'opponent': opponent}


async def remember_context(message_id, context):
    conn = await connect()
    try:
        await conn.execute('''INSERT INTO match_reminder_contexts
            (message_id, guild_id, owner_id, platform, game_id, players, opponent)
            VALUES ($1,$2,$3,$4,$5,$6::jsonb,$7) ON CONFLICT (message_id) DO NOTHING''',
            message_id, context['guild_id'], context['owner_id'], context['platform'],
            context['game_id'], json.dumps(context['players']), context['opponent'])
    finally:
        await conn.close()


async def get_context(message_id):
    conn = await connect()
    try:
        row = await conn.fetchrow('SELECT * FROM match_reminder_contexts WHERE message_id=$1', message_id)
        if row:
            result = dict(row)
            result['players'] = json.loads(result['players'])
            return result
    finally:
        await conn.close()


async def save_notes(context, selected, note):
    # Validate against the saved roster; never trust client-supplied player IDs.
    rows = [(context['guild_id'], context['owner_id'], context['platform'], p['puuid'],
             p['riot_id'], note, context['game_id']) for p in context['players']
            if p['puuid'] in selected]
    if not rows:
        raise ValueError('Select at least one player.')
    conn = await connect()
    try:
        async with conn.transaction():
            await conn.executemany('''INSERT INTO player_reminders
                (guild_id, owner_id, platform, puuid, riot_id, note, source_game_id)
                VALUES ($1,$2,$3,$4,$5,$6,$7)
                ON CONFLICT (guild_id, owner_id, platform, puuid) DO UPDATE SET
                riot_id=EXCLUDED.riot_id, note=EXCLUDED.note,
                source_game_id=EXCLUDED.source_game_id, updated_at=NOW()''', rows)
    finally:
        await conn.close()


async def reminder_embeds(context, budget=6000):
    conn = await connect()
    try:
        notes = await conn.fetch('''SELECT puuid, note FROM player_reminders
            WHERE guild_id=$1 AND owner_id=$2 AND platform=$3
            AND puuid=ANY($4::text[]) ORDER BY updated_at''',
            context['guild_id'], context['owner_id'], context['platform'],
            [p['puuid'] for p in context['players']])
    finally:
        await conn.close()
    if not notes:
        return []
    roster = {p['puuid']: p for p in context['players']}
    embed = discord.Embed(title='📝 Player reminders', color=discord.Color.gold())
    per_field = max(0, (budget - len(embed)) // len(notes))
    if per_field < 80:
        return []
    for row in notes:
        p = roster[row['puuid']]
        name = f"{p['riot_id']} · {p['champion']}"[:min(180, per_field // 2)]
        text = discord.utils.escape_markdown(row['note'])
        limit = min(1024, per_field - len(name))
        value = text if len(text) <= limit else text[:limit - 1] + '…'
        embed.add_field(name=name, value=value, inline=False)
    return [embed]


class ReminderModal(discord.ui.Modal, title='Write a player reminder'):
    note = discord.ui.TextInput(label='Reminder for selected players',
        style=discord.TextStyle.paragraph, max_length=500, min_length=1,
        placeholder='What should you remember next time you see them?')

    def __init__(self, context, selected):
        super().__init__(timeout=600)
        self.context = context
        self.selected = tuple(selected)

    async def on_submit(self, interaction):
        if interaction.user.id != self.context['owner_id'] or interaction.guild_id != self.context['guild_id']:
            await interaction.response.send_message('This reminder belongs to another user.', ephemeral=True)
            return
        note = self.note.value.strip()
        if not note:
            await interaction.response.send_message('Please write a reminder.', ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            await save_notes(self.context, self.selected, note)
        except Exception:
            log.exception('Could not save player reminder')
            await interaction.followup.send('Could not save the reminder. Please try again.', ephemeral=True)
            return
        await interaction.followup.send(f'Saved for {len(self.selected)} player(s). '
            'It will appear in future match messages when you see them again.', ephemeral=True)


class PlayerSelect(discord.ui.Select):
    def __init__(self, context):
        super().__init__(placeholder='Select or unselect players', min_values=0,
            max_values=len(context['players']), options=[discord.SelectOption(
                label=p['riot_id'][:100], value=p['puuid'],
                description=f"{p['team']} · {p['champion']}"[:100],
                default=p['puuid'] == context['opponent']) for p in context['players']])

    async def callback(self, interaction):
        self.view.selected = list(self.values)
        for option in self.options:
            option.default = option.value in self.values
        await interaction.response.edit_message(view=self.view)


class PlayerPicker(discord.ui.View):
    def __init__(self, context):
        super().__init__(timeout=600)
        self.context = context
        self.selected = [p['puuid'] for p in context['players'] if p['puuid'] == context['opponent']]
        self.add_item(PlayerSelect(context))

    async def interaction_check(self, interaction):
        if interaction.user.id == self.context['owner_id'] and interaction.guild_id == self.context['guild_id']:
            return True
        await interaction.response.send_message('This menu belongs to another user.', ephemeral=True)
        return False

    @discord.ui.button(label='Write reminder', style=discord.ButtonStyle.primary)
    async def write(self, interaction, button):
        if not self.selected:
            await interaction.response.send_message('Select at least one player first.', ephemeral=True)
            return
        await interaction.response.send_modal(ReminderModal(self.context, self.selected))


class MatchReminderView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Add player reminder', emoji='📝',
                       custom_id='leaguematch:player-reminder:v1')
    async def open_reminder(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        try:
            context = await get_context(interaction.message.id)
            if not context or not context['players']:
                await interaction.followup.send('No selectable players are available for this message.', ephemeral=True)
                return
            if interaction.user.id != context['owner_id'] or interaction.guild_id != context['guild_id']:
                await interaction.followup.send('Only the linked player for this message can add reminders.', ephemeral=True)
                return
            await interaction.followup.send('Select players, then choose **Write reminder**. '
                'Your lane opponent is selected by default. Saving replaces the previous note '
                'for each selected player; unselecting does not delete saved notes.',
                view=PlayerPicker(context), ephemeral=True)
        except Exception:
            log.exception('Could not open reminder menu')
            await interaction.followup.send('Could not open reminders. Please try again.', ephemeral=True)


async def send_match_message(send, embed, game, guild_id, owner_id, platform, puuid, **kwargs):
    context = await make_context(game, guild_id, owner_id, platform, puuid)
    reminders = await reminder_embeds(context, budget=6000 - len(embed))
    message = await send(embeds=[embed, *reminders], view=MatchReminderView(),
                         allowed_mentions=discord.AllowedMentions.none(), **kwargs)
    await remember_context(message.id, context)
    return message
