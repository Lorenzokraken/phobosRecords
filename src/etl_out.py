"""ETL Output: orchestrates royalty calculations and reporting."""

from .db import connect_db
from .etl.queries import calculate_royalties, calculate_artist_summary
from .etl.formatters import print_royalties, print_artist_summary
from .etl.logger import log_operation


@log_operation
def main():
    """Calculate and display royalty reports."""
    conn = connect_db()
    royalties = calculate_royalties(conn)
    summary = calculate_artist_summary(conn)
    conn.close()

    print("\n" + "="*85)
    print("DETTAGLIO TRANSAZIONI PER ROYALTY")
    print("="*85)
    print_royalties(royalties)

    print("\nRIASSUNTO PER ARTISTA (CON ADVANCE TRACKING)")
    print_artist_summary(summary)


if __name__ == "__main__":
    main()