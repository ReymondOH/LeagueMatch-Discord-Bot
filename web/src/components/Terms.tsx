export default function Terms() {
  return <>
    <div className="page-heading"><div><div className="eyebrow">TERMS OF USE</div><h1>Using LeagueMatch.</h1><p>Terms for the Discord bot and match insights website.</p></div></div>
    <article className="panel prose">
      <p>LeagueMatch is an independently developed League of Legends Discord bot and statistics website. The website displays aggregate match statistics from collected Riot match history. The bot remains a project under development, and its features may change.</p>
      <h2>Access and use</h2>
      <p>You may use the website to explore historical matchup results. Link only a Riot account you are authorized to use and install or configure the bot only in a Discord server where you have permission. Use LeagueMatch in accordance with the applicable Riot Games and Discord rules. The website does not ask for your Riot password or Discord token.</p>
      <h2>Announcements and controls</h2>
      <p>When tracking is enabled, the bot may post current match information in your server’s configured announcement channel. People with access to that channel may see the messages. You can disable automatic notifications with <code>/tracking</code> and remove your link in that server with <code>/unlink</code>. These commands do not remove past Discord announcements or automatically erase previously collected match data. See <a href="#privacy">Data &amp; privacy</a> for collection and deletion details.</p>
      <h2>Statistics and availability</h2>
      <p>The dashboard describes only matches in the collected sample. Win rates can change as matches are added, and small samples may be misleading. The bot, data collection, and website may be interrupted or changed; no particular level of availability or accuracy is promised. Statistics are informational and are not a guarantee of in-game results.</p>
      <h2>Third-party services and independence</h2>
      <p>LeagueMatch uses Riot Games data and operates alongside Discord. Their services have their own terms and policies. LeagueMatch is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.</p>
      <h2>Contact</h2>
      <p>For project questions or concerns, open an issue in the <a href="https://github.com/ReymondOH/LeagueMatch-Discord-Bot/issues" target="_blank" rel="noreferrer">LeagueMatch repository</a>. Keep passwords, API keys, and personal identifiers out of public issues. These terms may be updated as the project develops.</p>
      <p className="terms-updated">Last updated: September 24, 2026.</p>
    </article>
  </>;
}
