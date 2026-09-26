import asyncio
import itertools
import re

import discord

from database.database import get_saved_player_ranks, save_player_ranks
from services.riot_api import get_champion_names, get_player_rank
from services.setup_score import get_participant_setup_scores

SPELLS = {1: "Cleanse", 3: "Exhaust", 4: "Flash", 6: "Ghost",
          7: "Heal", 11: "Smite", 12: "Teleport", 13: "Clarity",
          14: "Ignite", 21: "Barrier", 32: "Snowball"}
KEYSTONES = {8005: "Press the Attack", 8008: "Lethal Tempo",
             8010: "Conqueror", 8021: "Fleet Footwork",
             8112: "Electrocute", 8124: "Predator", 8128: "Dark Harvest",
             9923: "Hail of Blades", 8214: "Summon Aery",
             8229: "Arcane Comet", 8230: "Phase Rush",
             8351: "Glacial Augment", 8360: "Unsealed Spellbook",
             8369: "First Strike", 8437: "Grasp of the Undying",
             8439: "Aftershock", 8465: "Guardian", 8992: "Deathfire Touch"}

TOP_CHAMPIONS = {
    "k'sante", "teemo", "aatrox", "akali", "ambessa", "camille",
    "cho'gath", "darius", "dr. mundo", "fiora", "gangplank", "garen",
    "gnar", "gragas", "gwen", "heimerdinger", "illaoi", "irelia",
    "jax", "jayce", "kayle", "kennen", "kled", "malphite",
    "mordekaiser", "nasus", "olaf", "ornn", "pantheon", "renekton",
    "riven", "rumble", "sett", "shen", "singed", "sion",
    "tahm kench", "trundle", "tryndamere", "urgot", "vayne",
    "volibear", "yasuo", "yone", "yorick", "zaahen",
}
# These champions commonly flex into other positions. Prefer a dedicated top
# champion when both are on the same team.
FLEX_TOP = {"akali", "gragas", "heimerdinger", "irelia", "olaf",
            "pantheon", "rumble", "tahm kench", "trundle", "vayne",
            "yasuo", "yone"}
JUNGLE_CHAMPIONS = {
    "shen", "amumu", "bel'veth", "briar", "cho'gath", "diana",
    "ekko", "elise", "evelynn", "fiddlesticks", "graves", "hecarim",
    "ivern", "jarvan iv", "karthus", "kayn", "kha'zix", "kindred",
    "lee sin", "lillia", "master yi", "naafiri", "nidalee", "nocturne",
    "nunu & willump", "qiyana", "quinn", "rammus", "rek'sai",
    "rengar", "sejuani", "shaco", "shyvana", "skarner", "sylas",
    "talon", "udyr", "vi", "viego", "warwick", "wukong",
    "xin zhao", "zac", "zed",
}
MID_CHAMPIONS = {
    "ryze", "smolder", "ahri", "akali", "akshan", "anivia", "annie",
    "aurelion sol", "aurora", "azir", "cassiopeia", "diana", "ekko",
    "fizz", "galio", "hwei", "irelia", "kassadin", "katarina",
    "leblanc", "lissandra", "locke", "lux", "malzahar", "mel",
    "nasus", "orianna", "qiyana", "sylas", "syndra", "taliyah",
    "twisted fate", "veigar", "vex", "viktor", "vladimir",
    "xerath", "yasuo", "yone", "zed", "zoe",
}
ADC_CHAMPIONS = {
    "aphelios", "senna", "smolder", "ashe", "caitlyn", "corki",
    "draven", "ezreal", "jhin", "jinx", "kai'sa", "kalista",
    "kog'maw", "lucian", "miss fortune", "nilah", "samira", "sivir",
    "tristana", "twitch", "varus", "vayne", "veigar", "viktor",
    "xayah", "yasuo", "yunara", "zeri", "ziggs",
}
SUPPORT_CHAMPIONS = {
    "alistar", "bard", "blitzcrank", "brand", "braum", "camille",
    "janna", "karma", "leona", "lulu", "lux", "maokai", "milio",
    "morgana", "nami", "nautilus", "neeko", "pantheon", "poppy",
    "pyke", "rakan", "rell", "renata glasc", "senna", "seraphine",
    "sona", "soraka", "swain", "tahm kench", "taric", "thresh",
    "vel'koz", "xerath", "yuumi", "zilean", "zyra",
}
ROLE_CHAMPIONS = {"TOP": TOP_CHAMPIONS, "JUNGLE": JUNGLE_CHAMPIONS,
                  "MID": MID_CHAMPIONS, "ADC": ADC_CHAMPIONS,
                  "SUPPORT": SUPPORT_CHAMPIONS}
ROLES = tuple(ROLE_CHAMPIONS)


def role_likelihood(player, role, team=None):
    participant, name, _, _ = player
    spells = {participant.get("spell1Id"), participant.get("spell2Id")}
    keystone = ((participant.get("perks") or {}).get("perkIds") or [None])[0]
    name = name.lower()
    eligible = name in ROLE_CHAMPIONS[role]
    possible_roles = sum(name in names for names in ROLE_CHAMPIONS.values())
    score = 4 + (2 if possible_roles == 1 else 0) if eligible else -7
    if role == "JUNGLE":
        score += 12 if 11 in spells else 0
    elif 11 in spells:
        score -= 1000
    if role == "TOP" and 12 in spells:
        score += 1
    if name in JUNGLE_CHAMPIONS and name in MID_CHAMPIONS and 11 not in spells:
        if role == "MID":
            score += 8
        elif role == "JUNGLE":
            score -= 8
    if name == "akali":
        top_setup = 12 in spells and keystone == 8010
        if role == "TOP":
            score += 10 if top_setup else -3
        elif role == "MID":
            score += -3 if top_setup else (9 if keystone == 8112 else 6)
    if name in {"irelia", "nasus", "cho'gath", "shen"} and role == "TOP":
        score += 6
    if name == "yone":
        other_top = any(other is not player and
                        other[1].lower() in TOP_CHAMPIONS and
                        other[1].lower() != "yone" and
                        11 not in {other[0].get("spell1Id"), other[0].get("spell2Id")}
                        for other in (team or []))
        if role == "TOP":
            score += -5 if other_top else 7
        elif role == "MID" and other_top:
            score += 7
    if name in {"camille", "pantheon", "tahm kench"}:
        other_top = any(other is not player and
                        other[1].lower() in TOP_CHAMPIONS and
                        11 not in {other[0].get("spell1Id"), other[0].get("spell2Id")}
                        for other in (team or []))
        other_support = any(other is not player and
                            other[1].lower() in SUPPORT_CHAMPIONS and
                            other[1].lower() not in {"camille", "pantheon", "tahm kench"}
                            for other in (team or []))
        favor_top = other_support or not other_top
        if role == "TOP" and favor_top:
            score += 8
        elif role == "SUPPORT" and not favor_top:
            score += 8
    if name in {"lux", "xerath"}:
        other_mid = any(other is not player and
                        other[1].lower() in MID_CHAMPIONS and
                        11 not in {other[0].get("spell1Id"), other[0].get("spell2Id")}
                        for other in (team or []))
        if role == "MID" and not other_mid:
            score += 8
        elif role == "SUPPORT" and other_mid:
            score += 8
    if name in {"smolder", "veigar", "viktor"}:
        other_mid = any(other is not player and
                        other[1].lower() in MID_CHAMPIONS and
                        11 not in {other[0].get("spell1Id"), other[0].get("spell2Id")}
                        for other in (team or []))
        if name == "smolder":
            other_adc = any(other is not player and
                            other[1].lower() in ADC_CHAMPIONS and
                            11 not in {other[0].get("spell1Id"), other[0].get("spell2Id")}
                            for other in (team or []))
            if role == "TOP" and other_adc and other_mid:
                score = 25  # Requested fallback even though TOP is not in the screenshot.
            elif role == "MID" and other_adc and not other_mid:
                score += 10
            elif role == "ADC" and not other_adc:
                score += 10
        elif role == "MID" and not other_mid:
            score += 8
        elif role == "ADC" and other_mid:
            score += 8
    if name == "vayne":
        other_adc = any(other is not player and
                        other[1].lower() in ADC_CHAMPIONS and
                        11 not in {other[0].get("spell1Id"), other[0].get("spell2Id")}
                        for other in (team or []))
        if role == "TOP" and other_adc:
            score += 8
        elif role == "ADC" and not other_adc:
            score += 8
    if name == "senna":
        other_adc = any(other is not player and
                        other[1].lower() in ADC_CHAMPIONS and
                        11 not in {other[0].get("spell1Id"), other[0].get("spell2Id")}
                        for other in (team or []))
        if role == "SUPPORT" and other_adc:
            score += 8
        elif role == "ADC" and not other_adc:
            score += 8
    if name == "yasuo":
        other_mid = any(other is not player and
                        other[1].lower() in MID_CHAMPIONS and
                        11 not in {other[0].get("spell1Id"), other[0].get("spell2Id")}
                        for other in (team or []))
        other_adc = any(other is not player and
                        other[1].lower() in ADC_CHAMPIONS and
                        11 not in {other[0].get("spell1Id"), other[0].get("spell2Id")}
                        for other in (team or []))
        preferred = "MID" if not other_mid else "ADC" if not other_adc else "TOP"
        if role == preferred:
            score += 12
    return score


def assign_roles(players):
    """Choose the best distinct champion for each role across the whole team."""
    if len(players) != len(ROLES):
        return {}, players
    best = max(itertools.permutations(range(len(players))),
               key=lambda assignment: sum(role_likelihood(players[index], role, players)
                                          for role, index in zip(ROLES, assignment)))
    return {role: players[index] for role, index in zip(ROLES, best)}, []


def indicator(result):
    if result is None:
        return "⚪❗"
    difference = result["score"] - result["baseline"]
    return "🟢❗" if difference >= 3 else "🔴❗" if difference <= -3 else "🟡❗"


def player_lines(participant, name, scores, rank):
    setup = scores["setup"]
    score = f"{setup['score']}/100" if setup else "N/A"
    spells = " + ".join(SPELLS.get(participant.get(key), str(participant.get(key, "?")))
                        for key in ("spell1Id", "spell2Id"))
    keystone_id = ((participant.get("perks") or {}).get("perkIds") or [None])[0]
    keystone = KEYSTONES.get(keystone_id, f"Rune {keystone_id or '?'}")
    player_id = discord.utils.escape_markdown(str(participant.get("riotId", "Unknown")))
    return (f"**{name} ({score})**\n"
            f"Spells: {spells} {indicator(scores['spells'])}\n"
            f"Keystone: {keystone} {indicator(scores['keystone'])}\n"
            f"{player_id} · {rank}")


def display_rank(rank):
    """Show divisions as numbers and omit I for apex tiers."""
    match = re.fullmatch(r"(\w+)\s+(I|II|III|IV)\s+\((\d+) LP\)", rank)
    if not match:
        return rank
    tier, division, lp = match.groups()
    if tier in {"Master", "Grandmaster", "Challenger"}:
        return f"{tier} ({lp} LP)"
    number = {"I": 1, "II": 2, "III": 3, "IV": 4}[division]
    return f"{tier} {number} ({lp} LP)"


async def create_match_embed(game, riot_id, platform, puuid=None):
    champion_names = await get_champion_names()
    participants = game.get("participants", [])
    teams = {100: [], 200: []}
    for participant in participants:
        champion_id = participant.get("championId")
        name = champion_names.get(champion_id, f"Champion {champion_id}")
        teams.setdefault(participant.get("teamId"), []).append(
            (participant, name, None, None))

    embed = discord.Embed(
        title="🎮 Live League Match",
        description=(f"**{discord.utils.escape_markdown(riot_id)}** has entered a game!\n"
                     "Score: historical setup win rate, not a match prediction.\n"
                     "🟢 above baseline · 🟡 near baseline · 🔴 below baseline · ⚪ insufficient data"),
    )
    blue_roles, _ = assign_roles(teams[100])
    red_roles, _ = assign_roles(teams[200])
    linked = next((player for side in teams.values() for player in side
                   if (puuid and player[0].get("puuid") == puuid)), None)
    if linked is None:
        linked = next((player for side in teams.values() for player in side
                       if player[0].get("riotId", "").casefold() == riot_id.casefold()), None)
    if linked is None:
        embed.add_field(name="Matchup unavailable",
                        value="Could not identify the linked player in this game.", inline=False)
        return embed

    own_roles = blue_roles if linked[0].get("teamId") == 100 else red_roles
    opponent_roles = red_roles if linked[0].get("teamId") == 100 else blue_roles
    role = next((name for name, player in own_roles.items()
                 if player[0] is linked[0]), None)
    opponent = opponent_roles.get(role) if role else None


    selected = [linked] + ([opponent] if opponent else [])
    semaphore = asyncio.Semaphore(3)
    others = [player[0]["puuid"] for side in teams.values() for player in side
              if player[0] is not linked[0] and player[0].get("puuid")]
    try:
        saved_ranks = await get_saved_player_ranks(others, platform)
    except Exception as error:
        print(f"Saved rank lookup unavailable: {error}")
        saved_ranks = {}
    newly_fetched = {}

    async def rank_for(player):
        puuid = player[0].get("puuid")
        if not puuid:
            return "Rank unavailable"
        saved_rank = saved_ranks.get(puuid) if player[0] is not linked[0] else None
        if saved_rank and "division/LP unavailable" not in saved_rank:
            return display_rank(saved_ranks[puuid])
        async with semaphore:
            try:
                rank = await get_player_rank(puuid, platform=platform)
                if rank not in {"Unknown", "Unranked"}:
                    newly_fetched[puuid] = rank
                    return display_rank(rank)
                return saved_rank or rank
            except Exception:
                return saved_rank or "Rank unavailable"

    all_players = teams[100] + teams[200]
    ranks, pair_scores = await asyncio.gather(
        asyncio.gather(*(rank_for(player) for player in all_players)),
        asyncio.gather(*(get_participant_setup_scores(player[0]) for player in selected),
                       return_exceptions=True),
    )
    if newly_fetched:
        try:
            await save_player_ranks(platform, newly_fetched)
        except Exception as error:
            print(f"Could not save rank lookups: {error}")
    rank_by_player = {id(player[0]): rank for player, rank in zip(all_players, ranks)}
    lines = []
    for player, scores in zip(selected, pair_scores):
        participant, name = player[:2]
        if isinstance(scores, Exception):
            scores = {"setup": None, "spells": None, "keystone": None}
        side = "🔵" if participant.get("teamId") == 100 else "🔴"
        lines.append(f"{side} {player_lines(participant, name, scores, rank_by_player[id(participant)])}")
    embed.add_field(name=f"{linked[1]} vs {opponent[1] if opponent else '?'}",
                    value="\n\n".join(lines), inline=False)

    for team_id, assignments in ((100, blue_roles), (200, red_roles)):
        remaining = ([assignments[name] for name in ROLES]
                     if assignments else teams[team_id])
        remaining = [player for player in remaining
                     if player[0] is not linked[0] and
                     (opponent is None or player[0] is not opponent[0])]
        team_lines = [f"{player[1]} - {rank_by_player[id(player[0])]}"
                      for player in remaining]
        embed.add_field(name="🔵 Blue Team" if team_id == 100 else "🔴 Red Team",
                        value="\n".join(team_lines) or "No other players", inline=False)
    embed.set_footer(text=f"Game ID: {game.get('gameId', '?')} · Opponent estimated")
    return embed
