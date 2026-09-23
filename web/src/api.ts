import demoData from './data/demo.json';
import type { Filters, Matchup, Observation, Stats } from './types';
export const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').trim().replace(/\/$/, '');
const pageSize = 8;
export const initialFilters: Filters = { champion_id: '', role: '', patch: '', page: 1 };
const patchSort = (a: string, b: string) => b.localeCompare(a, undefined, { numeric: true });
export function demoStats(filters: Filters): Stats {
  const data = demoData as Observation[];
  const rows = data.filter(r => (!filters.champion_id || r.champion_id === Number(filters.champion_id)) && (!filters.role || r.role === filters.role) && (!filters.patch || r.patch === filters.patch));
  const groups = new Map<string, Matchup>();
  for (const row of rows) {
    const key = `${row.champion_id}:${row.opponent_id}:${row.role}`;
    const group = groups.get(key) ?? { champion_id: row.champion_id, opponent_id: row.opponent_id, role: row.role, games: 0, wins: 0, win_rate: 0 };
    group.games++; group.wins += Number(row.win); groups.set(key, group);
  }
  const matchups = [...groups.values()].map(r => ({ ...r, win_rate: Math.round(r.wins / r.games * 1000) / 10 })).sort((a,b) => b.games-a.games || a.champion_id-b.champion_id || a.opponent_id-b.opponent_id || a.role.localeCompare(b.role));
  return {
    source: 'demo', summary: { matches: new Set(rows.map(r=>r.match_id)).size, observations: rows.length, champions: new Set(rows.map(r=>r.champion_id)).size, matchups: matchups.length },
    matchups: matchups.slice((filters.page-1)*pageSize, filters.page*pageSize), total: matchups.length, page: filters.page, page_size: pageSize,
    options: { champions: [...new Set(data.map(r=>r.champion_id))], roles: [...new Set(data.map(r=>r.role))], patches: [...new Set(data.map(r=>r.patch))].sort(patchSort) },
  };
}
export async function fetchStats(filters: Filters, mode: 'demo' | 'database', signal: AbortSignal): Promise<Stats> {
  if (mode === 'demo') return demoStats(filters);
  if (!API_BASE) throw new Error('The data service has not been connected yet.');
  const query = new URLSearchParams({ page: String(filters.page), page_size: String(pageSize) });
  if (filters.champion_id) query.set('champion_id', filters.champion_id);
  if (filters.role) query.set('role', filters.role);
  if (filters.patch) query.set('patch', filters.patch);
  const response = await fetch(`${API_BASE}/stats?${query}`, { signal });
  if (!response.ok) throw new Error(response.status === 503 ? 'The data service cannot reach its database. Try again later.' : 'The data service could not load these results.');
  const data: Stats = await response.json();
  if (!data.summary || !Array.isArray(data.matchups) || !data.options || !['demo','database'].includes(data.source)) throw new Error('The data service returned an unexpected response.');
  return data;
}
