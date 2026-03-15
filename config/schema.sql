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