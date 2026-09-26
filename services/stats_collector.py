from services.riot_api import (
    get_match_ids,
    get_match,
    get_solo_rank_tier
)

import asyncio

from database.database import save_match_stat, get_sample_puuids, add_rank_tier_column

rank_cache = {}


async def rank_for_participant(puuid, match_id):
    # Match IDs identify the platform, e.g. LA1_... or NA1_...
    platform = match_id.split("_", 1)[0].lower()
    if platform not in {"na1", "la1", "la2", "euw1", "eun1", "br1",
                        "tr1", "ru", "kr", "jp1", "oc1", "ph2", "sg2",
                        "th2", "tw2", "vn2"}:
        return None
    key = (platform, puuid)
    if key not in rank_cache:
        try:
            rank_cache[key] = await get_solo_rank_tier(puuid, platform)
        except RuntimeError as error:
            print(f"Cannot look up rank for this match: {error}")
            raise
        await asyncio.sleep(1.5)
    return rank_cache[key]

def find_opponent(participant, participants):

    for opponent in participants:

        if (
            opponent["teamId"] != participant["teamId"]
            and
            opponent["teamPosition"] == participant["teamPosition"]
        ):
            return opponent

    return None

async def collect_matches(puuid, count=5):

    match_ids = await get_match_ids(
        puuid,
        count=count
    )

    print(f"Found {len(match_ids)} matches")

    for match_id in match_ids:

        print(f"\nProcessing {match_id}")

        match = await get_match(match_id)

        if match is None:
            continue

        await asyncio.sleep(1.4)

        participants = match["info"]["participants"]
        queue_id = match["info"]["queueId"]

        game_version = match["info"]["gameVersion"]

        version_parts = game_version.split(".")
        patch = f"{version_parts[0]}.{version_parts[1]}"

        print(
            f"Queue ID: {queue_id} | "
            f"Participants: {len(participants)}"
        )

        if len(participants) != 10:
            print(
                f"Skipping {match_id}: "
                f"{len(participants)} participants"
            )
            continue

        if queue_id != 420:
            print(
                f"Skipping {match_id}: "
                f"Queue ID {queue_id}"
            )
            continue

        print(
            f"Found {len(participants)} participants"
        )

        for participant in participants:

            opponent = find_opponent(
                participant,
                participants
            )

            if opponent is None:
                continue

            keystone_id = (
                participant["perks"]["styles"][0]
                ["selections"][0]["perk"]
            )

            spell1_id = participant["summoner1Id"]
            spell2_id = participant["summoner2Id"]

            champion_id = participant["championId"]
            champion = participant["championName"]
            opponent_champion = opponent["championName"]
            puuid = participant["puuid"]
            rank_tier = await rank_for_participant(puuid, match_id)

            position = participant["teamPosition"]
            win = participant["win"]
            opponent_id = opponent["championId"]
            await save_match_stat(
                match_id,
                patch,
                champion_id,
                opponent_id,
                position,
                keystone_id,
                spell1_id,
                spell2_id,
                win,
                puuid,
                rank_tier
            )

            print(
                f"{champion} vs {opponent_champion} | "
                f"{position} | "
                f"Keystone: {keystone_id} | "
                f" Spells: {spell1_id} / {spell2_id}"
                f" patch: {patch} | Rank snapshot: {rank_tier or 'Unknown'} | "
                f"{'WIN' if win else 'LOSS'}"
            )

async def collect_from_multiple_players(
    player_limit=5,
    matches_per_player=10
):
    puuids = await get_sample_puuids(
        limit=player_limit
    )

    print(f"\nFound {len(puuids)} players to collect from")

    for index, puuid in enumerate(puuids, start=1):

        print(
            f"\n===== PLAYER {index}/{len(puuids)} ====="
        )

        await collect_matches(
            puuid,
            count=matches_per_player
        )

if __name__ == "__main__":
    import asyncio

    async def test():
        await add_rank_tier_column()
        await collect_from_multiple_players(
            player_limit=6,
            matches_per_player=10
        )

    asyncio.run(test())
