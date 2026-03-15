"""Pytest configuration and fixtures."""

import pytest
from src.db import connect_db


@pytest.fixture(scope="function")
def db_conn():
    """Create and cleanup test database connection."""
    conn = connect_db()
    
    # Truncate tables before test
    cur = conn.cursor()
    try:
        cur.execute("TRUNCATE TABLE quotas, transactions, works, artists RESTART IDENTITY CASCADE")
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()

    yield conn

    # Cleanup after test
    cur = conn.cursor()
    try:
        cur.execute("TRUNCATE TABLE quotas, transactions, works, artists RESTART IDENTITY CASCADE")
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
        conn.close()
