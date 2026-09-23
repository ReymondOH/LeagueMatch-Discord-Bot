import { useEffect, useState } from 'react';
import { ArrowDownRight, ArrowUpRight, ChevronLeft, ChevronRight, Database, Filter, RefreshCw, Search, ShieldCheck, Swords, Users, Layers3 } from 'lucide-react';
import { API_BASE, fetchStats, initialFilters } from '../api';
import { championName, roleName } from '../data/champions';
import type { Filters, Stats } from '../types';
const roles = ['', 'TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'];
export default function Dashboard() {
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [mode, setMode] = useState<'demo'|'database'>(API_BASE ? 'database' : 'demo');
  const [stats, setStats] = useState<Stats|null>(null);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState('');
  const [revision,setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    let timedOut = false;
    const timeout = setTimeout(()=>{ timedOut=true; controller.abort(); }, 12000);
    setLoading(true); setError('');
    fetchStats(filters,mode,controller.signal).then(result=>{ if (!controller.signal.aborted) setStats(result); }).catch(err=>{
      if (timedOut) setError('The data service took too long to respond. Try again.');
      else if (!controller.signal.aborted) setError(err instanceof Error ? err.message : 'Could not load the data.');
    }).finally(()=>{ clearTimeout(timeout); if (!controller.signal.aborted || timedOut) setLoading(false); });
    return ()=>{ clearTimeout(timeout); controller.abort(); };
  }, [filters,mode,revision]);
  const update = (key: 'champion_id'|'patch'|'role', value: string) => setFilters(f=>({...f,[key]:value,page:1}));
  const reset = ()=>setFilters({...initialFilters});
  const source = mode==='demo' ? 'demo' : stats?.source;
  const active = !!(filters.champion_id || filters.patch || filters.role);
  const metrics = [
    { label:'Matches analyzed',value:stats?.summary.matches,icon:Swords,note:'Distinct matches in this selection' },
    { label:'Player records',value:stats?.summary.observations,icon:Users,note:'One participant per match' },
    { label:'Champions',value:stats?.summary.champions,icon:ShieldCheck,note:'Champions represented' },
    { label:'Matchups',value:stats?.summary.matchups,icon:Layers3,note:'Champion, opponent, and role' },
  ];
  return <>
    <div className="page-heading"><div><div className="eyebrow">POST-MATCH ANALYSIS</div><h1>Explore the matchup.</h1><p>Understand historical results, one matchup at a time.</p></div><button className="button secondary refresh" onClick={()=>setRevision(v=>v+1)} disabled={loading}><RefreshCw size={16} className={loading?'spin':''}/> Refresh</button></div>
    <div className="dataset-banner"><div className="banner-icon"><Database size={19}/></div><div><strong>{source==='demo'?'You’re exploring a demo dataset.': 'Collected match data'}</strong><p>{source==='demo'?'Synthetic matches show how LeagueMatch works. These are not real player statistics.':'Results come from saved match history. Browsing does not make new Riot API requests.'}</p></div><span className="badge">{source==='demo'?'DEMO':'DATABASE'}</span></div>
    <div className="metrics" aria-live="polite">{metrics.map(({label,value,icon:Icon,note})=><article className="metric" key={label}><div className="metric-label">{label}<Icon size={17}/></div><strong>{loading||error?'—':value?.toLocaleString()??'0'}</strong><small>{note}</small></article>)}</div>
    <section className="panel"><div className="panel-heading"><div><h2>Matchup explorer</h2><p>Ranked solo · historical observations</p></div><div className="source-select"><label htmlFor="source">Data source</label><select id="source" value={mode} onChange={e=>{setMode(e.target.value as 'demo'|'database');setStats(null);reset();}}><option value="demo">Demo dataset</option><option value="database" disabled={!API_BASE}>Collected data{!API_BASE?' — not connected':''}</option></select></div></div>
      <div className="filters"><label className="filter"><span><Search size={15}/> Champion</span><select value={filters.champion_id} onChange={e=>update('champion_id',e.target.value)}><option value="">All champions</option>{stats?.options.champions.slice().sort((a,b)=>championName(a).localeCompare(championName(b))).map(id=><option key={id} value={id}>{championName(id)}</option>)}</select></label><label className="filter patch-filter"><span><Filter size={15}/> Patch</span><select value={filters.patch} onChange={e=>update('patch',e.target.value)}><option value="">All collected patches</option>{stats?.options.patches.map(p=><option key={p} value={p}>{p}</option>)}</select></label><button className="text-button reset" disabled={!active} onClick={reset}>Reset filters</button></div>
      <div className="roles" role="group" aria-label="Filter by role">{roles.map(role=><button key={role} aria-pressed={filters.role===role} className={filters.role===role?'selected':''} onClick={()=>update('role',role)}>{role?roleName(role):'All roles'}</button>)}</div>
      {loading?<div className="empty" role="status"><RefreshCw className="spin" size={26}/><h3>Loading matchups…</h3></div>:error?<div className="empty error" role="alert"><h3>Matchups couldn’t be loaded</h3><p>{error}</p><button className="button secondary" onClick={()=>setRevision(v=>v+1)}>Try again</button></div>:!stats?.matchups.length?<div className="empty"><Search size={30}/><h3>No matchups for this selection</h3><p>Try a different champion, role, or patch.</p><button className="button secondary" onClick={reset}>Clear filters</button></div>:<>
        <div className="table-scroll"><table><caption className="sr-only">Historical champion matchups, sorted by number of observations</caption><thead><tr><th scope="col">Matchup</th><th scope="col">Role</th><th scope="col">Observations</th><th scope="col">Win rate</th><th scope="col">Record</th></tr></thead><tbody>{stats.matchups.map(row=><tr key={`${row.champion_id}:${row.opponent_id}:${row.role}`}><td><div className="matchup-name"><span className="champion-monogram" aria-hidden="true">{championName(row.champion_id).slice(0,2)}</span><div><strong>{championName(row.champion_id)}</strong><span className="opponent">vs {championName(row.opponent_id)}</span></div></div></td><td><span className="role-tag">{roleName(row.role)}</span></td><td><strong className="tabular">{row.games.toLocaleString()}</strong><small className="sample-note">{row.games<100?'Small sample':'Collected records'}</small></td><td><div className="rate"><strong className={row.win_rate>=50?'positive':'negative'}>{row.win_rate.toFixed(1)}% {row.win_rate>=50?<ArrowUpRight size={14}/>:<ArrowDownRight size={14}/>}</strong><div className="rate-track" aria-hidden="true"><span style={{width:`${row.win_rate}%`}}/></div></div></td><td className="record"><span>{row.wins}W</span><span>{row.games-row.wins}L</span></td></tr>)}</tbody></table></div>
        <div className="pagination"><span>{(stats.page-1)*stats.page_size+1}–{Math.min(stats.page*stats.page_size,stats.total)} of {stats.total} matchups</span><div><button aria-label="Previous page" disabled={filters.page===1} onClick={()=>setFilters(f=>({...f,page:f.page-1}))}><ChevronLeft size={17}/></button><span>Page {stats.page} of {Math.ceil(stats.total/stats.page_size)}</span><button aria-label="Next page" disabled={stats.page*stats.page_size>=stats.total} onClick={()=>setFilters(f=>({...f,page:f.page+1}))}><ChevronRight size={17}/></button></div></div>
      </>}
    </section>
    <div className="below-grid"><article className="note-card"><span className="eyebrow">READING THE NUMBERS</span><h3>Context before conclusions.</h3><p>Win rate is wins divided by collected observations. Small samples and who was collected can skew results. These figures describe this dataset; they are not predictions or a replacement for Riot’s ranked ladder.</p></article><article className="note-card mint-card"><span className="eyebrow">YOUR DISCORD COMPANION</span><h3>Keep your server in the loop.</h3><p>Link a Riot ID and let LeagueMatch announce when a match starts.</p><a href="#about">Explore the bot <ArrowUpRight size={17}/></a></article></div>
  </>;
}
