"""Database operations: insert and lookup functions."""

from ..dataobjects import Artist, Work, Transaction
from dataclasses import asdict
from .logger import log_operation


@log_operation
def insert_artist(conn, artist: Artist):
    """Insert or update artist in DB."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO artists (name, royalty_pct, advance_paid, advance_pending,
                             is_front_artist, artist_image, main_genre, work_type, loaded_at)
        VALUES (%(name)s, %(royalty_pct)s, %(advance_paid)s, %(advance_pending)s,
                %(is_front_artist)s, %(artist_image)s, %(main_genre)s, %(work_type)s, %(loaded_at)s)
        ON CONFLICT (name) DO UPDATE SET
            royalty_pct = EXCLUDED.royalty_pct,
            advance_paid = EXCLUDED.advance_paid,
            advance_pending = EXCLUDED.advance_pending,
            is_front_artist = EXCLUDED.is_front_artist,
            artist_image = EXCLUDED.artist_image,
            main_genre = EXCLUDED.main_genre,
            work_type = EXCLUDED.work_type,
            loaded_at = EXCLUDED.loaded_at
        RETURNING artist_id
    """, asdict(artist))
    artist_id = cur.fetchone()[0]
    cur.close()
    return artist_id


@log_operation
def insert_work(conn, work: Work):
    """Insert or update work in DB."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO works (artist_id, title, secondary_artists_id, work_cover,
                           genre, bpm, iswc, song_key, release_date, duration, loaded_at)
        VALUES (%(artist_id)s, %(title)s, %(secondary_artists_id)s, %(work_cover)s,
                %(genre)s, %(bpm)s, %(iswc)s, %(song_key)s, %(release_date)s, %(duration)s, %(loaded_at)s)
        ON CONFLICT (artist_id, title) DO UPDATE SET
            work_cover = EXCLUDED.work_cover,
            genre = EXCLUDED.genre,
            bpm = EXCLUDED.bpm,
            iswc = EXCLUDED.iswc,
            song_key = EXCLUDED.song_key,
            release_date = EXCLUDED.release_date,
            duration = EXCLUDED.duration,
            loaded_at = EXCLUDED.loaded_at
        RETURNING work_id
    """, asdict(work))
    work_id = cur.fetchone()[0]
    cur.close()
    return work_id


@log_operation
def insert_transaction(conn, transaction: Transaction):
    """Insert transaction in DB."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions (work_id, period, gross_rev, source, platform_fee, distr_cost,
                                  is_artist_paid, purchase_month, platform, territory, streaming_source, loaded_at)
        VALUES (%(work_id)s, %(period)s, %(gross_rev)s, %(source)s, %(platform_fee)s, %(distr_cost)s,
                %(is_artist_paid)s, %(purchase_month)s, %(platform)s, %(territory)s, %(streaming_source)s, %(loaded_at)s)
        ON CONFLICT (work_id, period, source) DO UPDATE SET
            gross_rev = EXCLUDED.gross_rev,
            platform_fee = EXCLUDED.platform_fee,
            distr_cost = EXCLUDED.distr_cost,
            is_artist_paid = EXCLUDED.is_artist_paid,
            purchase_month = EXCLUDED.purchase_month,
            platform = EXCLUDED.platform,
            territory = EXCLUDED.territory,
            streaming_source = EXCLUDED.streaming_source,
            loaded_at = EXCLUDED.loaded_at
    """, asdict(transaction))
    cur.close()

@log_operation
def insert_quotas(conn, work_id: int, quotas: list, loaded_at):
    """Insert royalty splits for a work.

    Args:
        work_id: ID of the work
        quotas: List of dicts like [{'artist_id': 1, 'quota_pct': 70}, ...]
        loaded_at: Timestamp
    """
    from ..dataobjects import Quota

    cur = conn.cursor()
    for quota in quotas:
        quota_obj = Quota(
            work_id=work_id,
            artist_id=quota['artist_id'],
            quota_pct=quota['quota_pct'],
            loaded_at=loaded_at
        )
        cur.execute("""
            INSERT INTO quotas (work_id, artist_id, quota_pct, loaded_at)
            VALUES (%(work_id)s, %(artist_id)s, %(quota_pct)s, %(loaded_at)s)
            ON CONFLICT (work_id, artist_id) DO UPDATE SET
                quota_pct = EXCLUDED.quota_pct,
                loaded_at = EXCLUDED.loaded_at
        """, asdict(quota_obj))
    cur.close()


def get_artist_id(conn, name):
    """Lookup artist_id from DB by name."""
    cur = conn.cursor()
    cur.execute("SELECT artist_id FROM artists WHERE name = %s", (name,))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None


def get_work_id(conn, title):
    """Lookup work_id from DB by title."""
    cur = conn.cursor()
    cur.execute("SELECT work_id FROM works WHERE title = %s", (title,))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None

def get_quotas_for_work(conn, work_id: int):
    """Get all quotas for a work."""
    cur = conn.cursor()
    cur.execute("""
        SELECT artist_id, quota_pct FROM quotas 
        WHERE work_id = %s ORDER BY artist_id
    """, (work_id,))
    rows = cur.fetchall()
    cur.close()
    return rows
