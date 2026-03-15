"""Tests for ETL operations."""

import pytest
from datetime import datetime, date
from src.dataobjects import Artist, Work, Transaction, Quota
from src.etl.db_operations import (
    insert_artist,
    insert_work,
    insert_quotas,
    get_artist_id,
    get_work_id,
    get_quotas_for_work,
)


@pytest.fixture
def sample_artist():
    """Sample artist fixture."""
    return Artist(
        name="Test Artist",
        royalty_pct=0.70,
        advance_paid=5000.00,
        advance_pending=2000.00,
        is_front_artist=True,
        artist_image="http://test.jpg",
        main_genre="Electronic",
        work_type="album",
        loaded_at=datetime.now()
    )


@pytest.fixture
def sample_work():
    """Sample work fixture."""
    return Work(
        artist_id=1,
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


@pytest.fixture
def sample_transaction():
    """Sample transaction fixture."""
    return Transaction(
        work_id=1,
        period=date(2025, 6, 1),
        gross_rev=1000.00,
        source="Spotify",
        platform_fee=150.00,
        distr_cost=50.00,
        is_artist_paid=False,
        purchase_month="2025-06",
        platform="Spotify",
        territory="IT",
        streaming_source="audio",
        loaded_at=datetime.now()
    )


class TestInsertArtist:
    """Tests for insert_artist function."""

    def test_insert_artist_success(self, db_conn, sample_artist):
        """Test successful artist insertion."""
        artist_id = insert_artist(db_conn, sample_artist)
        assert artist_id is not None
        assert isinstance(artist_id, int)

    def test_insert_artist_duplicate_update(self, db_conn, sample_artist):
        """Test that duplicate artist is updated, not duplicated."""
        artist_id_1 = insert_artist(db_conn, sample_artist)
        # Update royalty percentage
        sample_artist.royalty_pct = 0.75
        artist_id_2 = insert_artist(db_conn, sample_artist)
        # Should be same ID
        assert artist_id_1 == artist_id_2

    def test_get_artist_id(self, db_conn, sample_artist):
        """Test getting artist ID by name."""
        insert_artist(db_conn, sample_artist)
        found_id = get_artist_id(db_conn, sample_artist.name)
        assert found_id is not None

    def test_get_artist_id_not_found(self, db_conn):
        """Test getting non-existent artist returns None."""
        found_id = get_artist_id(db_conn, "NonExistent")
        assert found_id is None


class TestInsertWork:
    """Tests for insert_work function."""

    def test_insert_work_success(self, db_conn, sample_artist, sample_work):
        """Test successful work insertion."""
        insert_artist(db_conn, sample_artist)
        work_id = insert_work(db_conn, sample_work)
        assert work_id is not None
        assert isinstance(work_id, int)

    def test_get_work_id(self, db_conn, sample_artist, sample_work):
        """Test getting work ID by title."""
        insert_artist(db_conn, sample_artist)
        insert_work(db_conn, sample_work)
        found_id = get_work_id(db_conn, sample_work.title)
        assert found_id is not None

    def test_get_work_id_not_found(self, db_conn):
        """Test getting non-existent work returns None."""
        found_id = get_work_id(db_conn, "NonExistent")
        assert found_id is None


class TestInsertQuotas:
    """Tests for insert_quotas function."""

    def test_insert_quotas_success(self, db_conn, sample_artist, sample_work):
        """Test successful quota insertion."""
        artist_id = insert_artist(db_conn, sample_artist)
        work_id = insert_work(db_conn, sample_work)

        quotas = [{"artist_id": artist_id, "quota_pct": 100}]
        insert_quotas(db_conn, work_id, quotas, datetime.now())

        found_quotas = get_quotas_for_work(db_conn, work_id)
        assert len(found_quotas) == 1
        assert found_quotas[0][0] == artist_id  # artist_id
        assert found_quotas[0][1] == 100  # quota_pct

    def test_insert_quotas_multi_artist(self, db_conn, sample_artist):
        """Test quota insertion for multi-artist split."""
        artist_id_1 = insert_artist(db_conn, sample_artist)

        sample_artist.name = "Test Artist 2"
        artist_id_2 = insert_artist(db_conn, sample_artist)

        # Create work
        work = Work(
            artist_id=artist_id_1,
            title="Collaboration",
            secondary_artists_id=str(artist_id_2),
            work_cover="http://cover.jpg",
            genre=["Electronic"],
            bpm=128,
            iswc="T-999.999.999",
            song_key="Am",
            release_date=date(2025, 6, 15),
            duration=240,
            loaded_at=datetime.now()
        )
        work_id = insert_work(db_conn, work)

        # Insert split
        quotas = [
            {"artist_id": artist_id_1, "quota_pct": 70},
            {"artist_id": artist_id_2, "quota_pct": 30}
        ]
        insert_quotas(db_conn, work_id, quotas, datetime.now())

        found_quotas = get_quotas_for_work(db_conn, work_id)
        assert len(found_quotas) == 2
        # Verify split
        assert sum(q[1] for q in found_quotas) == 100


