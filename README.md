# LeagueMatch

LeagueMatch collects ranked League of Legends match data through a Discord bot and displays aggregate champion matchup statistics in a React dashboard.

- **Bot:** Python, discord.py, Riot API; links accounts, tracks matches, and writes to PostgreSQL.
- **Dashboard:** React, TypeScript, Vite; filters matchups by champion, role, and patch.
- **Stats API:** FastAPI and asyncpg; reads aggregate results from the bot's `match_stats` table.

The [website](https://leaguematch-reymond.reymondeliasortiz.chatgpt.site) currently shows clearly labeled sample data while its hosted API and database are being set up. The API and dashboard are working together locally with PostgreSQL.

## Run locally

Install dependencies for the bot following its existing Python requirements, provide its Discord, Riot, and PostgreSQL credentials in a local `.env`, then run `python bot.py` from the repository root. Never commit credentials.

For the web project, see [web/README.md](web/README.md). On Windows PowerShell, in `web/` run `npm.cmd install` and `npm.cmd run dev`; start FastAPI in a second terminal as described there.

For the hosted database, API, and Riot application steps, see [web/DEPLOYMENT.md](web/DEPLOYMENT.md). The root [render.yaml](render.yaml) points Render at `web/`.

LeagueMatch is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties.
