import { useEffect, useState } from 'react';
import { ArrowUpRight, BarChart3, Bot, FileText, Github, ShieldCheck } from 'lucide-react';
import Brand from './components/Brand';
import Dashboard from './components/Dashboard';
import About from './components/About';
import Privacy from './components/Privacy';
import Terms from './components/Terms';

const pages = {
  dashboard: { title: 'Match insights', Icon: BarChart3 },
  about: { title: 'The Discord bot', Icon: Bot },
  privacy: { title: 'Data & privacy', Icon: ShieldCheck },
  terms: { title: 'Terms of use', Icon: FileText },
} as const;
type Page = keyof typeof pages;
function currentPage(): Page {
  const hash = location.hash.slice(1);
  return hash in pages ? hash as Page : 'dashboard';
}

export default function App() {
  const [page, setPage] = useState(currentPage);
  useEffect(() => {
    const onHash = () => {
      if (location.hash === '#main') return;
      setPage(currentPage());
      window.scrollTo({ top: 0, behavior: 'instant' });
    };
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);
  useEffect(() => { document.title = `LeagueMatch · ${pages[page].title}`; }, [page]);

  return <div className="app">
    <a href="#main" className="skip-link">Skip to content</a>
    <aside className="sidebar">
      <Brand />
      <div className="nav-label">WORKSPACE</div>
      <nav aria-label="Main navigation">
        {(Object.entries(pages) as [Page, typeof pages[Page]][]).map(([id, { Icon, title }]) =>
          <a key={id} href={`#${id}`} className={page === id ? 'nav-item active' : 'nav-item'} aria-current={page === id ? 'page' : undefined}>
            <Icon size={19} />{title}
          </a>
        )}
      </nav>
      <div className="sidebar-bottom">
        <div className="build-label">AN INDEPENDENT PROJECT</div>
        <p>Built for the games<br />you play together.</p>
        <a href="https://github.com/ReymondOH/LeagueMatch-Discord-Bot" target="_blank" rel="noreferrer"><Github size={17} /> Bot source <ArrowUpRight size={15} /></a>
      </div>
    </aside>
    <div className="main-column">
      <header className="topbar"><span>League of Legends <span className="slash">/</span> {pages[page].title}</span><span className="project-status">In development</span></header>
      <main id="main" tabIndex={-1}>{page === 'dashboard' ? <Dashboard /> : page === 'about' ? <About /> : page === 'privacy' ? <Privacy /> : <Terms />}</main>
      <footer>
        <div><Brand /><div className="footer-links"><a href="#terms">Terms of use</a><a href="#privacy">Data &amp; privacy</a></div></div>
        <p>LeagueMatch is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.</p>
        <small>Independent project by Reymond Ortiz</small>
      </footer>
    </div>
  </div>;
}
