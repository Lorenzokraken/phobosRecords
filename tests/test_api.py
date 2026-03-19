"""Tests for API endpoints using FastAPI TestClient."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestHealth:

    def test_health_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "OK"


class TestArtistsJSON:
    """Test endpoints che leggono da artists.json."""

    def test_list_artists_returns_list(self):
        response = client.get("/api/artists")
        assert response.status_code == 200
        data = response.json()
        assert "artists" in data
        assert isinstance(data["artists"], list)

    def test_list_artists_not_empty(self):
        response = client.get("/api/artists")
        assert len(response.json()["artists"]) > 0


class TestWorksJSON:
    """Test endpoints che leggono da works.json."""

    def test_list_works_returns_list(self):
        response = client.get("/api/works")
        assert response.status_code == 200
        data = response.json()
        assert "works" in data
        assert isinstance(data["works"], list)

    def test_list_works_not_empty(self):
        response = client.get("/api/works")
        assert len(response.json()["works"]) > 0


@pytest.mark.integration
class TestRevenueDB:
    """Test endpoint revenue (richiedono DB attivo)."""

    def test_tot_revenue_all(self):
        response = client.get("/tot_revenue")
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data
        assert data["year"] == "all"

    def test_tot_revenue_with_year(self):
        response = client.get("/tot_revenue?year=2025")
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2025
        assert data["total_revenue"] >= 0

    def test_tot_unit_sold_all(self):
        response = client.get("/tot_unit_sold")
        assert response.status_code == 200
        data = response.json()
        assert "total_units" in data
        assert data["total_units"] >= 0

    def test_get_top_artist(self):
        response = client.get("/get_top_artist")
        assert response.status_code == 200
        data = response.json()
        assert "artist_id" in data
        assert "artist_name" in data
        assert "total_revenue" in data

    def test_calculate_artist_revenue_all(self):
        response = client.get("/calculate_artist_revenue")
        assert response.status_code == 200
        data = response.json()
        assert "revenues" in data
        assert isinstance(data["revenues"], list)

    def test_calculate_artist_revenue_by_id(self):
        response = client.get("/calculate_artist_revenue?artist_id=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["revenues"]) <= 1

    def test_calculate_work_revenue_all(self):
        response = client.get("/calculate_work_revenue")
        assert response.status_code == 200
        data = response.json()
        assert "revenues" in data
        assert isinstance(data["revenues"], list)

    def test_calculate_artist_monthly_revenue(self):
        response = client.get("/calculate_artist_monthly_revenue")
        assert response.status_code == 200
        data = response.json()
        assert "revenues" in data
