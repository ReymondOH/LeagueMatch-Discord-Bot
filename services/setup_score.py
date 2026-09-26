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


def score_choice(rows, predicate):
    """Rate one choice against the champion's observed baseline."""
    matched = [row for row in rows if predicate(row)]
    high_games = sum(row["games"] for row in matched
                     if row["rank_tier"] in HIGH_TIERS)
    selected = rows if high_games < MIN_GAMES else [
        row for row in rows if row["rank_tier"] in HIGH_TIERS]
    matched = [row for row in selected if predicate(row)]
    games = sum(row["games"] for row in matched)
    if games < MIN_GAMES or sum(row["games"] for row in selected) < MIN_GAMES:
        return None
    base_weight = sum(row["games"] * WEIGHTS[row["rank_tier"]]
                      for row in selected)
    base_wins = sum(row["wins"] * WEIGHTS[row["rank_tier"]]
                    for row in selected)
    choice_weight = sum(row["games"] * WEIGHTS[row["rank_tier"]]
                        for row in matched)
    choice_wins = sum(row["wins"] * WEIGHTS[row["rank_tier"]]
                      for row in matched)
    return {"score": round(100 * (choice_wins + PRIOR_GAMES * base_wins / base_weight)
                           / (choice_weight + PRIOR_GAMES)),
            "baseline": 100 * base_wins / base_weight, "games": games}


async def get_participant_setup_scores(participant):
    perks = participant.get("perks") or {}
    keystone = (perks.get("perkIds") or [None])[0]
    spell1, spell2 = participant.get("spell1Id"), participant.get("spell2Id")
    if not (participant.get("championId") and keystone and spell1 and spell2):
        return {"setup": None, "spells": None, "keystone": None}
    rows = await get_setup_stats(participant["championId"])
    low, high = sorted((spell1, spell2))
    return {
        "setup": score_setup(rows, keystone, spell1, spell2),
        "spells": score_choice(rows, lambda row: row["spell_low"] == low
                               and row["spell_high"] == high),
        "keystone": score_choice(rows, lambda row: row["keystone_id"] == keystone),
    }


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
