export type Role = 'TOP' | 'JUNGLE' | 'MIDDLE' | 'BOTTOM' | 'UTILITY';
export type Filters = { champion_id: string; role: string; patch: string; page: number };
export type Matchup = { champion_id: number; opponent_id: number; role: Role; games: number; wins: number; win_rate: number };
export type Stats = {
  source: 'demo' | 'database';
  summary: { matches: number; observations: number; champions: number; matchups: number };
  matchups: Matchup[]; total: number; page: number; page_size: number;
  options: { champions: number[]; roles: string[]; patches: string[] };
};
export type Observation = { match_id: string; patch: string; champion_id: number; opponent_id: number; role: Role; win: boolean };
