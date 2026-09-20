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