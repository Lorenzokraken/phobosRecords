"""Database queries for royalty calculations."""

from .logger import log_operation


@log_operation
def calculate_royalties(conn):
    """Calculate transaction-level royalties con quotas e advance logic."""
    cur = conn.cursor()
    query = """
    SELECT
        a.artist_id,
        a.name,
        a.royalty_pct,
        a.advance_paid,
        a.advance_pending,
        w.title,
        t.period,
        t.source,
        t.platform,
        t.territory,
        t.gross_rev,
        COALESCE(t.platform_fee, 0) as platform_fee,
        COALESCE(t.distr_cost, 0) as distr_cost,
        t.gross_rev - COALESCE(t.platform_fee, 0) - COALESCE(t.distr_cost, 0) AS net_rev,
        (t.gross_rev - COALESCE(t.platform_fee, 0) - COALESCE(t.distr_cost, 0)) * a.royalty_pct AS royalty_earned
    FROM transactions t
    JOIN works w ON t.work_id = w.work_id
    JOIN artists a ON w.artist_id = a.artist_id
    ORDER BY a.name, w.title, t.period
    """
    cur.execute(query)
    columns = [desc[0] for desc in cur.description]
    rows = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    return rows


@log_operation
def calculate_artist_summary(conn):
    """Aggregate royalties per artista con advance tracking."""
    cur = conn.cursor()
    query = """
    SELECT
        a.artist_id,
        a.name,
        a.advance_paid,
        a.advance_pending,
        SUM(t.gross_rev - COALESCE(t.platform_fee, 0) - COALESCE(t.distr_cost, 0)) * a.royalty_pct AS total_royalty_earned,
        COUNT(DISTINCT t.transaction_id) AS num_transactions,
        MIN(t.period) AS first_period,
        MAX(t.period) AS last_period
    FROM artists a
    LEFT JOIN works w ON a.artist_id = w.artist_id
    LEFT JOIN transactions t ON w.work_id = t.work_id
    GROUP BY a.artist_id, a.name, a.advance_paid, a.advance_pending
    ORDER BY a.name
    """
    cur.execute(query)
    columns = [desc[0] for desc in cur.description]
    rows = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    return rows
