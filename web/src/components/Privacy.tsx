export default function Privacy() {
  return <>
    <div className="page-heading"><div><div className="eyebrow">DATA & PRIVACY</div><h1>What LeagueMatch uses.</h1><p>How the bot, collector, and public dashboard handle data.</p></div></div>
    <article className="panel prose">
      <p className="terms-updated">Last updated: September 24, 2026.</p>
      <h2>Website visitors</h2>
      <p>You can browse the dashboard without signing in. It shows aggregated match statistics from collected League of Legends match history. The public statistics API returns totals and matchup results; it does not return Discord IDs, Riot IDs, or participant PUUIDs. The site does not use advertising trackers or analytics cookies. Its hosting providers may process basic connection and request information to deliver the site and API.</p>
      <h2>Discord bot and account links</h2>
      <p>When you use <code>/link</code>, the bot stores your Discord user ID, server ID, Riot ID, Riot PUUID, and platform. It also stores your tracking preference and last notified game ID. For each configured server, it stores the announcement channel ID. While tracking is enabled, the bot checks whether Discord shows you playing League of Legends and requests current game data from Riot. Match announcements sent to the selected channel are visible to people who can access that channel.</p>
      <h2>Match collection</h2>
      <p>A separate collector requests match history from Riot and stores ranked solo match IDs, patch, champion and opponent IDs, role, keystone, summoner spells, win or loss, and participant PUUIDs in PostgreSQL. If a scheduled collector is enabled, it can add more matches without a website visit. Stored PUUIDs support collection and analysis but are not returned by the public dashboard API. Riot and Discord process information under their own privacy terms when their services are used.</p>
      <h2>Storage and access</h2>
      <p>The database is hosted by Neon, the statistics API by Render, and the website by Vercel. Authorized project services use the database; website visitors receive only aggregate statistics. The project does not currently set an automatic deletion period for stored account links or match records.</p>
      <h2>Your controls and deletion requests</h2>
      <p>Use <code>/tracking</code> to disable automatic match announcements for your link and <code>/unlink</code> to remove your account link from that Discord server. Unlinking does not automatically delete previously collected match records or messages already posted to Discord. To request deletion of stored records associated with your account, contact the maintainer through the <a href="https://github.com/ReymondOH/LeagueMatch-Discord-Bot/issues" target="_blank" rel="noreferrer">project repository</a>. Do not post account identifiers, passwords, tokens, or other private details in a public issue; ask for a private way to provide the information needed to identify your records.</p>
      <h2>Changes</h2>
      <p>This notice may be updated as the project changes. The date above shows when this version was last updated.</p>
    </article>
  </>;
}
