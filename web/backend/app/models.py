from enum import Enum
from typing import Literal
from pydantic import BaseModel

class Role(str, Enum):
    TOP = 'TOP'
    JUNGLE = 'JUNGLE'
    MIDDLE = 'MIDDLE'
    BOTTOM = 'BOTTOM'
    UTILITY = 'UTILITY'

class Summary(BaseModel):
    matches: int
    observations: int
    champions: int
    matchups: int

class Matchup(BaseModel):
    champion_id: int
    opponent_id: int
    role: Role
    games: int
    wins: int
    win_rate: float

class Options(BaseModel):
    champions: list[int]
    roles: list[str]
    patches: list[str]

class StatsResponse(BaseModel):
    source: Literal['demo', 'database']
    summary: Summary
    matchups: list[Matchup]
    total: int
    page: int
    page_size: int
    options: Options
