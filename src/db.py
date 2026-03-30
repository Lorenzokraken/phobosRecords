import psycopg2
from psycopg2 import pool
import os
from dotenv import load_dotenv

load_dotenv()

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            _pool = pool.ThreadedConnectionPool(2, 10, database_url)
        else:
            _pool = pool.ThreadedConnectionPool(2, 10,
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 5432)),
                database=os.getenv("DB_NAME", "phobos_records"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "airvana")
            )
    return _pool

def connect_db():
    """Return a new connection to the PostgreSQL database (used by non-request code)."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "phobos_records"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "airvana")
    )

def get_db():
    p = get_pool()
    conn = p.getconn()
    try:
        yield conn
    finally:
        p.putconn(conn)
def create_tables():
    """Create the necessary tables in the database if they don't exist."""
    conn = connect_db()
    cur = conn.cursor()

    # Leggi lo schema da schema.sql
    import os
    schema_path = os.path.join(os.path.dirname(__file__), "..", "config", "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    cur.execute(schema_sql)

    conn.commit()
    cur.close()
    conn.close()
    print("✓ Tables created successfully")

def truncate_tables():
    """Delete all data from existing tables."""
    conn = connect_db()
    cur = conn.cursor()
    
    # Tronca tutte le tabelle (la materialized view aggregated_royalties si refresha separatamente)
    tables = ['transactions', 'works', 'artists']
    for table in tables:
        cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
    
    conn.commit()
    cur.close()
    conn.close()
    print("✓ Tables truncated successfully")

def refresh_aggregated_royalties():
    """Refresh the aggregated_royalties materialized view.
    Uses CONCURRENTLY (non-blocking) if already populated, plain refresh on first run.
    """
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT ispopulated FROM pg_matviews
        WHERE matviewname = 'aggregated_royalties'
    """)
    already_populated = cur.fetchone()[0]
    if already_populated:
        cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY aggregated_royalties")
    else:
        cur.execute("REFRESH MATERIALIZED VIEW aggregated_royalties")
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM aggregated_royalties")
    rows = cur.fetchone()[0]
    cur.close()
    conn.close()
    return rows


if __name__ == "__main__":
    truncate_tables()  # Cancella dati esistenti
    create_tables()  