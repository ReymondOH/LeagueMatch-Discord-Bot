import os
import aiohttp
from dotenv import load_dotenv


load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")


async def get_account_by_riot_id(game_name, tag_line):

    url = (
        f"https://americas.api.riotgames.com"
        f"/riot/account/v1/accounts/by-riot-id/"
        f"{game_name}/{tag_line}"
    )

    headers = {
        "X-Riot-Token": RIOT_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:

            if response.status == 200:
                return await response.json()

            print(f"Riot API Error: {response.status}")
            return None

async def get_current_game(puuid, platform="la1"):
    url = (
        f"https://{platform}.api.riotgames.com"
        f"/lol/spectator/v5/active-games/by-summoner/{puuid}"
    )

    headers = {
        "X-Riot-Token": RIOT_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:

            if response.status == 200:
                return await response.json()

            if response.status == 404:
                return None

            error_text = await response.text()

            print(f"Spectator API Error: {response.status}")
            print(f"Response: {error_text}")

            return None

async def get_current_game(puuid, platform="la1"):

    url = (
        f"https://{platform}.api.riotgames.com"
        f"/lol/spectator/v5/active-games/by-summoner/{puuid}"
    )

    headers = {
        "X-Riot-Token": RIOT_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:

            if response.status == 200:
                return await response.json()

            if response.status == 404:
                return None

            error_text = await response.text()

            print(f"Spectator API Error: {response.status}")
            print(f"Response: {error_text}")

            return None

async def get_champion_names():
    url = "https://ddragon.leagueoflegends.com/cdn/16.18.1/data/en_US/champion.json"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:

            if response.status != 200:
                print(f"Data Dragon Error: {response.status}")
                return {}

            data = await response.json()

            champion_names = {}

            for champion in data["data"].values():
                champion_names[int(champion["key"])] = champion["name"]

            return champion_names

async def get_player_rank(puuid, platform="la1"):
    url = (
        f"https://{platform}.api.riotgames.com"
        f"/lol/league/v4/entries/by-puuid/{puuid}"
    )

    headers = {
        "X-Riot-Token": RIOT_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:

            if response.status == 200:
                ranked_data = await response.json()

                for queue in ranked_data:
                    if queue["queueType"] == "RANKED_SOLO_5x5":
                        tier = queue["tier"]
                        rank = queue["rank"]
                        lp = queue["leaguePoints"]

                        return f"{tier.title()} {rank} ({lp} LP)"

                return "Unranked"

            error_text = await response.text()

            print(f"Rank API Error: {response.status}")
            print(f"Response: {error_text}")

            return "Unknown"