-- Optional: run manually against the same database your bot uses.
-- Existing match records are preserved. The API never runs migrations automatically.
BEGIN;
CREATE TABLE IF NOT EXISTS match_stats (
    id SERIAL PRIMARY KEY,
    match_id VARCHAR(100) NOT NULL,
    patch VARCHAR(20) NOT NULL,
    champion_id INTEGER NOT NULL,
    opponent_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,
    keystone_id INTEGER NOT NULL,
    spell1_id INTEGER NOT NULL,
    spell2_id INTEGER NOT NULL,
    win BOOLEAN NOT NULL,
    puuid VARCHAR(100),
    UNIQUE(match_id, champion_id)
);
-- One of the uploaded bot's older table definitions did not include puuid.
ALTER TABLE match_stats ADD COLUMN IF NOT EXISTS puuid VARCHAR(100);
CREATE INDEX IF NOT EXISTS idx_match_stats_dashboard ON match_stats (champion_id, role, patch);
COMMIT;
