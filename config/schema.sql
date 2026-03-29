CREATE TABLE IF NOT EXISTS artists (
    artist_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    royalty_pct NUMERIC(5,2) NOT NULL,
    advance_paid NUMERIC(10,2) NOT NULL DEFAULT 0,
    advance_pending NUMERIC(10,2) NOT NULL DEFAULT 0,
    is_front_artist BOOLEAN NOT NULL DEFAULT FALSE,
    artist_image TEXT NOT NULL,
    main_genre TEXT NOT NULL,
    work_type TEXT NOT NULL,
    loaded_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS works (
    work_id SERIAL PRIMARY KEY,
    artist_id INTEGER NOT NULL REFERENCES artists(artist_id),
    title TEXT NOT NULL,
    secondary_artists_id TEXT NOT NULL,
    work_cover TEXT NOT NULL,
    genre TEXT[] NOT NULL,
    bpm INTEGER NOT NULL,
    iswc TEXT NOT NULL,
    song_key TEXT NOT NULL,
    release_date DATE NOT NULL,
    duration INTEGER NOT NULL,
    loaded_at TIMESTAMP NOT NULL,
    UNIQUE(artist_id, title)
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(work_id),
    period DATE NOT NULL,
    gross_rev NUMERIC(10,2) NOT NULL,
    source TEXT NOT NULL,
    platform_fee NUMERIC(10,2),
    distr_cost NUMERIC(10,2),
    is_artist_paid BOOLEAN NOT NULL DEFAULT FALSE,
    purchase_month TEXT NOT NULL,
    platform TEXT NOT NULL,
    territory CHAR(2) NOT NULL,
    streaming_source TEXT NOT NULL,
    loaded_at TIMESTAMP NOT NULL,
    UNIQUE(work_id, period, source)
);

CREATE TABLE IF NOT EXISTS quotas (
    quota_id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(work_id),
    artist_id INTEGER NOT NULL REFERENCES artists(artist_id),
    quota_pct NUMERIC(5,2) NOT NULL,
    loaded_at TIMESTAMP NOT NULL,
    UNIQUE(work_id, artist_id)
);

CREATE MATERIALIZED VIEW IF NOT EXISTS aggregated_royalties AS
SELECT
    a.artist_id,
    a.name                                                              AS artist_name,
    a.royalty_pct,
    a.main_genre,
    w.work_id,
    w.title                                                             AS work_title,
    t.purchase_month,
    MAX(EXTRACT(YEAR FROM t.period)::INTEGER)                           AS period_year,
    t.platform,
    COALESCE(SUM(t.gross_rev), 0)                                       AS gross_rev,
    COALESCE(SUM(t.gross_rev
        - COALESCE(t.platform_fee, 0)
        - COALESCE(t.distr_cost,  0)), 0)                               AS net_rev,
    COALESCE(SUM(t.gross_rev
        - COALESCE(t.platform_fee, 0)
        - COALESCE(t.distr_cost,  0)), 0) * a.royalty_pct               AS royalty_earned,
    COUNT(t.transaction_id)                                             AS units_sold
FROM artists a
JOIN works        w ON a.artist_id  = w.artist_id
JOIN transactions t ON w.work_id    = t.work_id
WHERE t.purchase_month IS NOT NULL
GROUP BY
    a.artist_id, a.name, a.royalty_pct, a.main_genre,
    w.work_id,   w.title,
    t.purchase_month, t.platform
WITH NO DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_agg_pk
    ON aggregated_royalties(artist_id, work_id, purchase_month, platform);
CREATE INDEX IF NOT EXISTS idx_agg_artist   ON aggregated_royalties(artist_id);
CREATE INDEX IF NOT EXISTS idx_agg_year     ON aggregated_royalties(period_year);
CREATE INDEX IF NOT EXISTS idx_agg_platform ON aggregated_royalties(platform);
CREATE INDEX IF NOT EXISTS idx_agg_genre    ON aggregated_royalties(main_genre);
CREATE INDEX IF NOT EXISTS idx_agg_work     ON aggregated_royalties(work_id);