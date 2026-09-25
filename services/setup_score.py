"""Descriptive rune/spell setup score from collected ranked solo matches."""

from database.database import get_setup_stats

MIN_GAMES = 20
PRIOR_GAMES = 20
HIGH_TIERS = {"CHALLENGER", "GRANDMASTER", "MASTER", "DIAMOND"}
WEIGHTS = {"CHALLENGER": 1.5, "GRANDMASTER": 1.35,
           "MASTER": 1.2, "DIAMOND": 1.0, "EMERALD": 0.65}


def score_setup(rows, keystone_id, spell1_id, spell2_id):
    """Return None if this exact setup has insufficient observations.

    The score is a smoothed historical win percentage, NOT a win prediction.
    """
    low, high = sorted((spell1_id, spell2_id))
    matched = [row for row in rows if row["keystone_id"] == keystone_id
               and row["spell_low"] == low and row["spell_high"] == high]
    high_games = sum(row["games"] for row in matched
                     if row["rank_tier"] in HIGH_TIERS)
    include_emerald = high_games < MIN_GAMES
    selected = (rows if include_emerald else
                [row for row in rows if row["rank_tier"] in HIGH_TIERS])
    selected_matched = [row for row in selected if row in matched]
    games = sum(row["games"] for row in selected_matched)
    if games < MIN_GAMES:
        return None
    baseline_games = sum(row["games"] for row in selected)
    if baseline_games < MIN_GAMES:
        return None
    baseline_weight = sum(row["games"] * WEIGHTS[row["rank_tier"]]
                          for row in selected)
    baseline_wins = sum(row["wins"] * WEIGHTS[row["rank_tier"]]
                        for row in selected)
    match_weight = sum(row["games"] * WEIGHTS[row["rank_tier"]]
                       for row in selected_matched)
    match_wins = sum(row["wins"] * WEIGHTS[row["rank_tier"]]
                     for row in selected_matched)
    baseline = baseline_wins / baseline_weight
    score = round(100 * (match_wins + PRIOR_GAMES * baseline)
                  / (match_weight + PRIOR_GAMES))
    return {"score": score, "games": games, "baseline_games": baseline_games,
            "emerald_fallback": include_emerald,
            "emerald_games": sum(row["games"] for row in selected_matched
                                 if row["rank_tier"] == "EMERALD")}


async def get_live_setup_score(game, puuid):
    """Score the linked player only, if live data identifies their setup."""
    participant = next((p for p in game.get("participants", [])
                        if p.get("puuid") == puuid), None)
    if participant is None:
        return None
    perks = participant.get("perks", {})
    keystone = (perks.get("perkIds") or [None])[0]
    if not keystone or not participant.get("spell1Id") or not participant.get("spell2Id"):
        return None
    rows = await get_setup_stats(participant["championId"])
    return score_setup(rows, keystone, participant["spell1Id"], participant["spell2Id"])
