# Publish LeagueMatch with collected data

The React website is already deployed privately with a synthetic demo. The following steps connect a hosted Python API to a hosted PostgreSQL database and make new observations available when your bot writes them. Do not put a database URL, a Discord token, or a Riot key in the React environment or GitHub.

## 1. Prepare the single repository

The Discord bot stays at the repository root. The website, including `backend/`, belongs in `web/`. The Render service configuration is in the repository's root `render.yaml`. Pushing the website source to GitHub does **not** connect your private database automatically.

## 2. Create a hosted PostgreSQL database

Create a PostgreSQL project with an external connection URL (for example, Neon). Pick a region close to your bot and your API. Use the **direct** connection URL (not a pooler endpoint) for this asyncpg application. Keep it private. The Neon Free plan has usage and storage limits; check the current terms before relying on it for continuous service.

In pgAdmin, back up your local bot tables `linked_accounts`, `guild_settings`, and `match_stats`, then restore the backup into the hosted database. These tables contain member identifiers and PUUIDs; treat backups as sensitive, do not upload them to GitHub or the public website, and delete disposable local exports once restoration is verified. If you prefer to start fresh, run `web/backend/sql/schema.sql` in the hosted database, and let the bot create its two other tables. A fresh database starts with no historical stats or account links.

Check that `match_stats` contains the same number of rows in both databases after restoration. The existing bot's `database/database.py` schema bug (missing comma before `UNIQUE`) must be fixed before starting against a fresh hosted database. If creating `match_stats` from an older bot version, the `puuid` column must be present. The prepared repository change includes this fix.

## 3. Point the local bot to the hosted database

In the bot's local `.env`, use the hosted database's host, port, database name, username, and password for `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`, and add `PGSSLMODE=require`. asyncpg reads `PGSSLMODE` from the process environment. Restart the bot. Confirm `/link` and `/live` still work, and that the collector writes a new record to the hosted `match_stats` table. The database should not be exposed publicly just to serve the dashboard; connect to it using the provider's connection URL and SSL.

> Keep your existing `.env` file on your computer. Do not copy it into the website, a ZIP shared publicly, or Git.

## 4. Deploy FastAPI

In [Render](https://dashboard.render.com/), create a Blueprint from the single GitHub repository's **main** branch using the included `render.yaml`. It creates one Python web service and asks you for `DATABASE_URL`. Paste the hosted database's direct connection string into Render's **secret environment setting**, never into the YAML or a Git commit. The Blueprint sets `DEMO_MODE=false`, `DB_SSL=require`, and the website's CORS origin.

The service starts with `uvicorn` on Render's assigned `$PORT`. Open `https://YOUR-API.onrender.com/api/health`. It must return `{"status":"ok","source":"database"}`. Next open `/api/stats` and check that `summary.matches` and `summary.observations` are positive. If the health route returns 503, inspect service logs and database settings. A free Render web service can spin down when idle and take about a minute to respond to its next request. Consider a paid service if review reliability matters.

The API must only expose aggregate results. Use a dedicated database user with SELECT access to `match_stats` when the provider supports it, and set that account's URL as `DATABASE_URL` for the API. The bot still needs a user that can insert and update records.

## 5. Connect the hosted React site

In the **website build**, set the public configuration variable to the Render API origin, for example:

```dotenv
VITE_API_BASE_URL=https://YOUR-API.onrender.com/api
```

Rebuild and redeploy the website. The frontend now selects collected data by default. Check that the site shows a `DATABASE` badge and the same nonzero totals as `/api/stats`. The API URL is public; no credentials belong in a `VITE_` variable. If CORS fails, make sure Render's `CORS_ORIGINS` is the exact HTTPS origin of the published website, with no trailing slash.

Do not set this variable to `http://localhost:8000/api` on a hosted build. `localhost` in a visitor's browser refers to that visitor's computer.

## 6. Submit a public site for Riot review

Check the bot overview, Privacy page, Terms page, current feature status, and test access instructions. Then change the Site audience to public and open it in a private browsing window. A private Site URL cannot be reviewed by Riot. The Terms and Privacy text should reflect your actual operation before you submit it.

Riot's [production application guidance](https://support-developer.riotgames.com/hc/en-us/articles/22801383038867-Production-Key-Applications) asks for a functioning site with a visible product flow, Terms of Service, and Privacy Policy, including for Discord bots. After submitting the application, Riot provides a verification string. Put that exact string in `web/public/riot.txt` (or in this Site source at `public/riot.txt`), rebuild and republish, and verify that `https://YOUR-SITE-ORIGIN/riot.txt` shows the string. Do not add a placeholder file before Riot supplies the text. Riot then verifies site ownership. A production key is an application decision made by Riot; deploying the site does not grant one.

## Run locally without affecting production

Keep `web/.env` set to `VITE_API_BASE_URL=/api` and `web/backend/.env` set to your preferred local database settings. These ignored files do not alter the deployed build. Restart Vite or FastAPI when changing their environment files.
