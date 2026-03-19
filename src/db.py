import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def connect_db():
    """Return a new connection to the PostgreSQL database."""
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
    conn = connect_db()
    try:
        yield conn
    finally:
        conn.close()
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
    
    # Tronca tutte le tabelle (inclusa quotas)
    tables = ['transactions', 'works', 'artists']
    for table in tables:
        cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
    
    conn.commit()
    cur.close()
    conn.close()
    print("✓ Tables truncated successfully")

if __name__ == "__main__":
    truncate_tables()  # Cancella dati esistenti
    create_tables()  