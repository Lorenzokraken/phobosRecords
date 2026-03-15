"""ETL Input: orchestrates data loading from JSON and CSV sources."""

from .db import connect_db
from datetime import datetime
from .etl.data_loaders import load_artists, load_works, load_transactions, load_quotas
from .etl.logger import log_operation


@log_operation
def main():
    """Carica tutto in sequenza: artisti → opere → transazioni → quotas."""
    conn = connect_db()
    loaded_at = datetime.now()
    load_artists(conn, loaded_at)
    load_works(conn, loaded_at)
    load_quotas(conn, loaded_at)
    load_transactions(conn, loaded_at)
    conn.commit()
    conn.close()
    print("\n✓ Data saved successfully to database.")

if __name__ == "__main__":
    main()