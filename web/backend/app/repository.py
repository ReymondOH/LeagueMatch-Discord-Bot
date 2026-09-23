"""Aggregate queries only. Never select PUUIDs or Discord/account identifiers."""
import json
from pathlib import Path
from typing import Any
import asyncpg


def aggregate_demo(champion_id=None, role=None, patch=None, page=1, page_size=8):
    path = Path(__file__).resolve().parents[2] / 'src' / 'data' / 'demo.json'
    data = json.loads(path.read_text())
    rows = [r for r in data if (champion_id is None or r['champion_id'] == champion_id)
            and (role is None or r['role'] == role) and (patch is None or r['patch'] == patch)]
    groups = {}
    for row in rows:
        key = (row['champion_id'], row['opponent_id'], row['role'])
        group = groups.setdefault(key, dict(champion_id=key[0], opponent_id=key[1], role=key[2], games=0, wins=0))
        group['games'] += 1
        group['wins'] += int(row['win'])
    matchups = sorted(groups.values(), key=lambda g: (-g['games'], g['champion_id'], g['opponent_id'], g['role']))
    for group in matchups:
        group['win_rate'] = round(100 * group['wins'] / group['games'], 1)
    return dict(source='demo', summary=dict(matches=len({r['match_id'] for r in rows}),
        observations=len(rows), champions=len({r['champion_id'] for r in rows}), matchups=len(matchups)),
        matchups=matchups[(page-1)*page_size:page*page_size], total=len(matchups), page=page,
        page_size=page_size, options=dict(champions=sorted({r['champion_id'] for r in data}),
        roles=sorted({r['role'] for r in data}), patches=sorted({r['patch'] for r in data},
        key=lambda p:tuple(map(int,p.split('.'))), reverse=True)))


WHERE = """($1::int IS NULL OR champion_id = $1)
    AND ($2::text IS NULL OR role = $2)
    AND ($3::text IS NULL OR patch = $3)
    AND role IN ('TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY')"""


async def database_stats(pool: asyncpg.Pool, champion_id=None, role=None, patch=None, page=1, page_size=8) -> dict[str, Any]:
    params = (champion_id, role, patch)
    async with pool.acquire() as connection:
        # Consistent summary, rows and pagination even while the collector inserts.
        async with connection.transaction(isolation='repeatable_read', readonly=True):
            summary = dict(await connection.fetchrow(f"""
                SELECT COUNT(DISTINCT match_id)::int AS matches, COUNT(*)::int AS observations,
                    COUNT(DISTINCT champion_id)::int AS champions,
                    COUNT(DISTINCT (champion_id, opponent_id, role))::int AS matchups
                FROM match_stats WHERE {WHERE}
            """, *params))
            records = await connection.fetch(f"""
                SELECT champion_id, opponent_id, role, COUNT(*)::int AS games,
                    COUNT(*) FILTER (WHERE win)::int AS wins,
                    ROUND(100.0 * COUNT(*) FILTER (WHERE win) / COUNT(*), 1)::float8 AS win_rate
                FROM match_stats WHERE {WHERE}
                GROUP BY champion_id, opponent_id, role
                ORDER BY games DESC, champion_id, opponent_id, role
                LIMIT $4 OFFSET $5
            """, *params, page_size, (page-1)*page_size)
            options = await connection.fetchrow("""
                SELECT ARRAY_AGG(DISTINCT champion_id ORDER BY champion_id) AS champions,
                    ARRAY_AGG(DISTINCT role ORDER BY role) AS roles,
                    ARRAY_AGG(DISTINCT patch ORDER BY patch) AS patches
                FROM match_stats WHERE role IN ('TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY')
            """)
    def patch_key(value):
        try:
            return tuple(map(int, value.split('.')))
        except ValueError:
            return (0,)
    return dict(source='database', summary=summary, matchups=[dict(row) for row in records],
        total=summary['matchups'], page=page, page_size=page_size,
        options=dict(champions=options['champions'] or [], roles=options['roles'] or [],
            patches=sorted(options['patches'] or [], key=patch_key, reverse=True)))
