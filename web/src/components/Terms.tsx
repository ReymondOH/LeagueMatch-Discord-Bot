export default function Terms() {
  return <>
    <div className="page-heading"><div><div className="eyebrow">TERMS OF USE</div><h1>Using LeagueMatch.</h1><p>Terms for the Discord bot and match insights website.</p></div></div>
    <article className="panel prose">
      <p>LeagueMatch is an independently developed League of Legends Discord bot and statistics website. The bot is currently in testing. The dashboard may show a clearly labeled synthetic demo dataset until its hosted data service is connected.</p>
      <h2>Access and use</h2>
      <p>You may use the website to explore historical matchup results. If you use the Discord bot, link only a Riot account that you are authorized to use, and install the bot only in a server where you have permission. Follow Discord’s and Riot Games’ applicable rules while using LeagueMatch.</p>
      <h2>Announcements and controls</h2>
      <p>When you link an account and tracking is enabled, match information may be posted in your server’s configured announcement channel. Other members of that server may see those messages. You can stop automatic notifications with <code>/tracking</code> and remove your server account link with <code>/unlink</code>. Past announcements may remain in Discord. See <a href="#privacy">Data &amp; privacy</a> for information about collected records.</p>
      <h2>Statistics and availability</h2>
      <p>Win rates describe the collected sample and can change as matches are added. Small samples can be misleading. LeagueMatch is offered as a prototype; features and availability may change. Statistics are informational and do not dictate in-game decisions.</p>
      <h2>Contact</h2>
      <p>For project questions, report an issue in the <a href="https://github.com/ReymondOH/LeagueMatch-Discord-Bot/issues" target="_blank" rel="noreferrer">LeagueMatch repository</a>. Keep passwords, API keys, and other private details out of public issues.</p>
      <p className="terms-updated">Last updated: September 23, 2026.</p>
    </article>
  </>;
}
