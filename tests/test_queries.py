"""Tests for ETL queries."""

import pytest
from datetime import datetime, date
from src.dataobjects import Artist, Work, Transaction
from src.etl.db_operations import (
    insert_artist,
    insert_work,
    insert_transaction,
    insert_quotas,
)
from src.etl.queries import calculate_royalties, calculate_artist_summary


class TestCalculateRoyalties:
    """Tests for royalty calculation."""

    def test_calculate_royalties_empty(self, db_conn):
        """Test royalty calculation with no data."""
        royalties = calculate_royalties(db_conn)
        assert isinstance(royalties, list)
        assert len(royalties) == 0

    def test_calculate_royalties_single_transaction(self, db_conn):
        """Test royalty calculation with single transaction."""
        # Setup: create artist, work, transaction
        artist = Artist(
            name="Test Artist",
            royalty_pct=0.70,
            advance_paid=0.00,
            advance_pending=0.00,
            is_front_artist=True,
            artist_image="http://test.jpg",
            main_genre="Electronic",
            work_type="album",
            loaded_at=datetime.now()
        )
        artist_id = insert_artist(db_conn, artist)

        work = Work(
            artist_id=artist_id,
            title="Test Track",
            secondary_artists_id="",
            work_cover="http://cover.jpg",
            genre=["Electronic"],
            bpm=128,
            iswc="T-123.456.789",
            song_key="Am",
            release_date=date(2025, 6, 15),
            duration=240,
            loaded_at=datetime.now()
        )
        work_id = insert_work(db_conn, work)

        transaction = Transaction(
            work_id=work_id,
            period=date(2025, 6, 1),
            gross_rev=1000.00,
            source="Spotify",
            platform_fee=100.00,
            distr_cost=50.00,
            is_artist_paid=False,
            purchase_month="2025-06",
            platform="Spotify",
            territory="IT",
            streaming_source="audio",
            loaded_at=datetime.now()
        )
        insert_transaction(db_conn, transaction)

        royalties = calculate_royalties(db_conn)
        assert len(royalties) == 1
        
        row = royalties[0]
        expected_net_rev = 1000.00 - 100.00 - 50.00  # 850
        expected_royalty = expected_net_rev * 0.70  # 595
        
        assert row['net_rev'] == expected_net_rev
        assert row['royalty_earned'] == expected_royalty


class TestCalculateArtistSummary:
    """Tests for artist summary calculation."""

    def test_calculate_artist_summary_empty(self, db_conn):
        """Test summary with no data."""
        summary = calculate_artist_summary(db_conn)
        assert isinstance(summary, list)
        assert len(summary) == 0

    def test_calculate_artist_summary_no_transactions(self, db_conn):
        """Test summary with artist but no transactions."""
        artist = Artist(
            name="Test Artist",
            royalty_pct=0.70,
            advance_paid=1000.00,
            advance_pending=500.00,
            is_front_artist=True,
            artist_image="http://test.jpg",
            main_genre="Electronic",
            work_type="album",
            loaded_at=datetime.now()
        )
        insert_artist(db_conn, artist)

        summary = calculate_artist_summary(db_conn)
        assert len(summary) == 1
        assert summary[0]['name'] == "Test Artist"
        assert summary[0]['total_royalty_earned'] is None  # No transactions
