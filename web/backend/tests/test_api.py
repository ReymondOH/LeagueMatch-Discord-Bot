from fastapi.testclient import TestClient
from app.main import create_app


def test_demo_counts_distinct_matches_and_paginated_groups():
    with TestClient(create_app(demo_mode=True)) as client:
        data = client.get('/api/stats').json()
        assert data['source'] == 'demo'
        assert data['summary']['matches'] == 24
        assert data['summary']['observations'] == 240
        assert len(data['matchups']) == 8
        second = client.get('/api/stats?page=2').json()
        keys = lambda rows: {(r['champion_id'], r['opponent_id'], r['role']) for r in rows}
        assert keys(data['matchups']).isdisjoint(keys(second['matchups']))


def test_combined_filters_and_win_rate():
    with TestClient(create_app(demo_mode=True)) as client:
        data = client.get('/api/stats?champion_id=22&role=BOTTOM&patch=16.18').json()
        assert data['total'] == 1
        row = data['matchups'][0]
        assert row['champion_id'] == 22
        assert row['opponent_id'] == 51
        assert row['games'] == 12
        assert row['wins'] == 8
        assert row['win_rate'] == 66.7
        assert data['summary']['matches'] == 12
        assert data['summary']['observations'] == 12
        assert '16.17' in data['options']['patches']


def test_empty_and_out_of_range_pages_are_valid():
    with TestClient(create_app(demo_mode=True)) as client:
        empty = client.get('/api/stats?champion_id=22&role=TOP').json()
        assert empty['summary']['matches'] == 0
        assert empty['matchups'] == []
        assert client.get('/api/stats?page=9000').json()['matchups'] == []


def test_validation_and_private_identifiers():
    with TestClient(create_app(demo_mode=True)) as client:
        for query in ['page=0','page_size=999','champion_id=-1','role=INVALID','patch=16.18%27%3B']:
            assert client.get('/api/stats?'+query).status_code == 422
        body = client.get('/api/stats').text
        for private_key in ['puuid','discord_id','riot_id','guild_id']:
            assert private_key not in body


class BrokenPool:
    async def fetchval(self, _):
        raise RuntimeError('secret connection details')


def test_database_failure_never_falls_back_to_fake_results():
    with TestClient(create_app(demo_mode=False, supplied_pool=BrokenPool())) as client:
        response = client.get('/api/stats')
        assert response.status_code == 503
        assert 'secret' not in response.text
        assert 'demo' not in response.text
        assert client.get('/api/health').status_code == 503


def test_cors_allows_only_configured_origin():
    with TestClient(create_app(demo_mode=True)) as client:
        allowed = client.get('/api/health', headers={'Origin':'http://localhost:5173'})
        assert allowed.headers['access-control-allow-origin'] == 'http://localhost:5173'
        other = client.get('/api/health', headers={'Origin':'https://unrelated.example'})
        assert 'access-control-allow-origin' not in other.headers
