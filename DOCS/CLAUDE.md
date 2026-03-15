PHOBOS RECORDS: Da 3.9/10 a 9/10
Piano per impressionare recruiter tecnico + settore musicale
TIER 1: Production Fundamentals (3.9 → 7) [10h]
1. README con Architecture Diagram (2h) - MASSIMO ROI
markdown# Phobos Records - Royalty Management System

Real-world data engineering solution for independent music label.

## Architecture

[Diagram showing: JSON/CSV → ETL → PostgreSQL → FastAPI → Frontend]

## Tech Stack
- Python 3.11 + FastAPI
- PostgreSQL 15
- Docker Compose
- Pytest + logging

## Features
✅ Multi-source revenue tracking (streaming, live, merch, sync)
✅ Multi-artist royalty split
✅ Advance recoupment calculation
✅ Territory-based revenue
✅ Real-time API dashboard

## Quick Start
```bash
docker-compose up -d
python etl_in.py
python main.py
# Open http://localhost:8000
```

**Perché spacca:** Recruiter vede SUBITO valore + deployment facile

#### 2. Docker Compose (2h) - **DEPLOYMENT READY**
```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: phobos_records
      POSTGRES_USER: phobos
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - ./schema.sql:/docker-entrypoint-initdb.d/schema.sql
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://phobos:${DB_PASSWORD}@postgres:5432/phobos_records
    ports:
      - "8000:8000"
    volumes:
      - ./:/app
    command: uvicorn main:app --host 0.0.0.0 --reload

volumes:
  postgres_data:
```

**Perché spacca:** "Faccio `docker-compose up` e funziona subito" = production mindset

#### 3. Error Handling + Logging (3h) - **PRODUCTION QUALITY**
```python
# etl_in.py refactor
import logging
from typing import Optional

logging.basicConfig(
    filename='logs/etl.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ETLError(Exception):
    """Custom ETL exception"""
    pass

def insert_artist(conn, artist: Artist) -> Optional[int]:
    """Insert artist with error handling"""
    try:
        cur = conn.cursor()
        cur.execute("""...""", asdict(artist))
        artist_id = cur.fetchone()[0]
        logger.info(f"Inserted artist {artist.name} with ID {artist_id}")
        return artist_id
    except psycopg2.IntegrityError as e:
        logger.error(f"Duplicate artist {artist.name}: {e}")
        conn.rollback()
        return None
    except Exception as e:
        logger.error(f"Failed to insert artist {artist.name}: {e}")
        conn.rollback()
        raise ETLError(f"Artist insert failed: {e}")
    finally:
        cur.close()

def main():
    try:
        conn = connect_db()
        # ETL logic...
        conn.commit()
        logger.info("ETL completed successfully")
    except ETLError as e:
        logger.critical(f"ETL failed: {e}")
        sys.exit(1)
    finally:
        conn.close()
```

**Perché spacca:** "Ha gestito errori in produzione" = senior mindset

#### 4. Pytest Test Suite (3h) - **QUALITY ASSURANCE**
```python
# tests/test_etl.py
import pytest
from etl_in import insert_artist, calculate_net_revenue
from dataobjects import Artist

@pytest.fixture
def db_conn():
    """Test database connection"""
    conn = connect_db("test_phobos")
    yield conn
    conn.rollback()
    conn.close()

def test_insert_artist_success(db_conn):
    artist = Artist(
        name="Test Artist",
        royalty_pct=0.70,
        advance_paid=5000,
        advance_pending=5000,
        is_front_artist=True,
        artist_image="http://test.jpg",
        main_genre="Electronic",
        work_type="album",
        loaded_at=datetime.now()
    )
    artist_id = insert_artist(db_conn, artist)
    assert artist_id is not None

def test_advance_recoupment():
    """Test advance deduction logic"""
    gross_royalty = 3000
    advance_pending = 2000
    expected_payout = 1000
    
    result = calculate_net_revenue(gross_royalty, advance_pending)
    assert result == expected_payout

# Run: pytest tests/ -v --cov=. --cov-report=html
```

**Perché spacca:** "Ha test coverage >70%" = sa sviluppare correttamente

---

### TIER 2: Advanced Features (7 → 9) [8h]

#### 5. Advance Recoupment Logic (4h) - **DOMAIN EXPERTISE**
```python
# etl_out.py - NEW
def calculate_artist_payout(artist_id: int, period: str) -> dict:
    """Calculate artist payout with advance recoupment"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get total royalties for period
    cur.execute("""
        SELECT 
            a.name,
            a.advance_pending,
            SUM(
                (t.gross_rev - t.platform_fee - t.distr_cost) * q.quota_pct
            ) AS gross_royalty
        FROM transactions t
        JOIN quotas q ON t.work_id = q.work_id
        JOIN artists a ON q.artist_id = a.artist_id
        WHERE a.artist_id = %s AND t.period = %s
        GROUP BY a.artist_id, a.name, a.advance_pending
    """, (artist_id, period))
    
    result = cur.fetchone()
    
    gross_royalty = result['gross_royalty']
    advance_pending = result['advance_pending']
    
    # Advance recoupment logic
    if advance_pending > 0:
        if gross_royalty >= advance_pending:
            # Recover full advance
            net_payout = gross_royalty - advance_pending
            advance_remaining = 0
        else:
            # Partial recovery
            net_payout = 0
            advance_remaining = advance_pending - gross_royalty
    else:
        # No advance to recover
        net_payout = gross_royalty
        advance_remaining = 0
    
    return {
        'artist': result['name'],
        'period': period,
        'gross_royalty': float(gross_royalty),
        'advance_recovered': float(advance_pending - advance_remaining),
        'advance_remaining': float(advance_remaining),
        'net_payout': float(net_payout)
    }
```

**Perché spacca:** "Capisce la logica business della label" = non è solo dev, è domain expert

#### 6. Multi-Artist Split (quotas table) (2h) - **REAL-WORLD SCENARIO**
```python
# etl_in.py - NEW
def insert_quotas(conn, work_id: int, splits: list[dict]):
    """Insert royalty splits for multi-artist works
    
    Example:
        splits = [
            {'artist_id': 1, 'quota_pct': 0.70},  # Main artist
            {'artist_id': 2, 'quota_pct': 0.30}   # Featured artist
        ]
    """
    cur = conn.cursor()
    for split in splits:
        try:
            cur.execute("""
                INSERT INTO quotas (work_id, artist_id, quota_pct, loaded_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (work_id, artist_id) DO UPDATE
                SET quota_pct = EXCLUDED.quota_pct
            """, (work_id, split['artist_id'], split['quota_pct'], datetime.now()))
            logger.info(f"Inserted quota {split['quota_pct']} for work {work_id}")
        except Exception as e:
            logger.error(f"Failed to insert quota: {e}")
            raise
```

**Perché spacca:** "60% release hanno featured artist" = risolve problema reale

#### 7. GitHub Actions CI/CD (2h) - **DEVOPS READY**
```yaml
# .github/workflows/ci.yml
name: CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:test_password@localhost:5432/test_phobos
      run: |
        pytest tests/ -v --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

**Perché spacca:** "Pipeline CI/CD funzionante" = sa DevOps base

---

## PIANO PARALLELO (3 settimane Databricks + Phobos)

### Week 1: Foundation
- **Databricks:** Unity Catalog (3h/day)
- **Phobos:** README + Docker Compose (1-2h total spread over week)

### Week 2: Quality
- **Databricks:** Lakeflow + Workflows (3h/day)
- **Phobos:** Error handling + Logging (1-2h total)

### Week 3: Advanced
- **Databricks:** Practice exam prep (3h/day)
- **Phobos:** Advance logic + Tests (1-2h total)

### Week 4: Polish (post-exam)
- **Phobos:** CI/CD + final touches (4h total)
- **Deploy:** README polish + screenshots

**Totale Phobos: ~18h spalmato su 4 settimane = 1h/day mediamente**

---

## DELIVERABLE FINALE (9/10)

**Cosa vede il recruiter su GitHub:**
phobos-records/
├── README.md              ← Architecture diagram, quick start
├── docker-compose.yml     ← One-command deployment
├── .github/workflows/     ← CI/CD pipeline
├── tests/                 ← Test coverage >70%
├── logs/                  ← Structured logging
├── db.py                  ← Schema completo (quotas)
├── etl_in.py              ← Error handling + logging
├── etl_out.py             ← Advance recoupment logic
├── main.py                ← FastAPI + endpoints
└── frontend/              ← Dashboard funzionante

**Badge README:**
- ✅ CI/CD passing
- ✅ Test coverage 75%+
- ✅ Docker ready
- ✅ MIT License

---

## COSA SPACCA DAVVERO (priorità visiva)

1. **README con diagram** = primo impatto in 10 secondi
2. **Docker Compose** = "lo faccio girare subito" in 1 comando
3. **CI/CD badge** = "questo è serio"
4. **Test coverage** = "sa sviluppare bene"
5. **Advance logic** = "capisce il dominio"