"""Formatting and printing functions for royalty reports."""

from .logger import log_operation


@log_operation
def print_royalties(royalties):
    """Print transaction-level royalties."""
    print(f"{'Name':<15} {'Title':<20} {'Period':<12} {'Source':<12} {'Gross':>10} {'Royalty':>10}")
    print("-" * 85)
    for row in royalties:
        print(
            f"{row['name']:<15} "
            f"{row['title']:<20} "
            f"{str(row['period']):<12} "
            f"{row['source']:<12} "
            f"€{row['gross_rev']:>8.2f} "
            f"€{row['royalty_earned']:>8.2f}"
        )


@log_operation
def print_artist_summary(summary):
    """Print per-artist summary con advance tracking."""
    print("\n" + "="*100)
    print(f"{'ARTIST':<20} {'TOTAL EARNED':>15} {'ADVANCE PAID':>15} {'ADVANCE PENDING':>15} {'RECOVERABLE':>15} {'NET ROYALTY':>15}")
    print("-" * 100)

    for row in summary:
        if row['total_royalty_earned'] is None:
            continue
        total = row['total_royalty_earned']
        advance_pending = row['advance_pending']
        recoverable = min(total, advance_pending)
        net_royalty = total - recoverable

        print(
            f"{row['name']:<20} "
            f"€{total:>13.2f} "
            f"€{row['advance_paid']:>13.2f} "
            f"€{advance_pending:>13.2f} "
            f"€{recoverable:>13.2f} "
            f"€{net_royalty:>13.2f}"
        )
