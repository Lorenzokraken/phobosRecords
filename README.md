# Phobos Records – Royalty Management System

A comprehensive ETL-based royalty calculation and tracking system for independent music labels. Manages artist royalties, advance payments, and multi-artist splits across multiple streaming platforms.

## Features

- **Transaction-level royalty calculation** – Process streaming revenue from multiple platforms
- **Multi-artist splits** – Handle co-written tracks with quota-based revenue distribution
- **Advance recoupment tracking** – Monitor advance payments and recoverable amounts
- **Comprehensive reporting** – Transaction detail and per-artist summary views
- **Automatic data import** – ETL pipeline with validation and error handling
- **Modular architecture** – Clean separation of concerns (DB operations, ETL, queries, formatting)

## Architecture

```
data/
├── artists.json           # Artist metadata and royalty percentages
├── works.json            # Track metadata with multi-artist quotas
└── transaction.csv       # Platform streaming/purchase transactions

etl/
├── logger.py             # Centralized logging with @log_operation decorator
├── db_operations.py      # Database insert/lookup functions
├── data_loaders.py       # ETL extraction and transformation
├── queries.py            # Royalty calculation queries
└── formatters.py         # Report output formatting

etl_in.py                 # Input orchestrator: loads data files → DB
etl_out.py                # Output orchestrator: calculates → reports
db.py                     # Database connection manager
dataobjects.py            # Data class definitions (Artist, Work, Transaction, Quota)
```

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

## Setup

### 1. Install Dependencies

```bash
pip install psycopg2-binary pytest python-dotenv
```

### 2. Configure Database

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=phobos_records
DB_USER=postgres
DB_PASSWORD=your_password
```

### 3. Start PostgreSQL

**Via Docker Compose** (recommended):

```bash
docker-compose up -d
```

**Or manually:**

```bash
# macOS (Homebrew)
brew services start postgresql@15

# Linux (systemd)
sudo systemctl start postgresql

# Windows
# Use PostgreSQL installer or pgAdmin
```

### 4. Initialize Database

Run the schema setup:

```bash
py -c "from db import init_db; init_db()"
```

This creates the required tables: `artists`, `works`, `transactions`, and `quotas`.

## Usage

### Load Data (ETL Input)

```bash
python etl_in.py
```

This sequentially:
1. Loads artists from `data/artists.json`
2. Loads works from `data/works.json`
3. Loads multi-artist quotas from works.json
4. Loads transactions from `data/transaction.csv`

**Output:**
```
✓ Artista inserito: Lyra Void (ID: 1)
  ✓ Opera inserita: Event Horizon (ID: 1)
  ✓ Quotas inserite per opera: Event Horizon
    ✓ Transazione: Apple Music - Event Horizon (42356$)
```

### Generate Reports (ETL Output)

```bash
python etl_out.py
```

Displays two reports:

**1. Transaction Details**
```
Name            Title                Period       Source       Gross        Royalty
Lyra Void       Dark Matter          2026-02-01   Spotify      €32,100.00   €3,852.00
Lyra Void       Quantum Dreams       2026-02-01   Deezer       €18,900.00   €2,268.00
...
```

**2. Artist Summary (with Advance Tracking)**
```
ARTIST               TOTAL EARNED    ADVANCE PAID  ADVANCE PENDING  RECOVERABLE  NET ROYALTY
Lyra Void             €45,620.50      €5,000.00      €2,000.00        €2,000.00   €43,620.50
Echo Waves            €52,380.25      €4,000.00      €1,800.00        €1,800.00   €50,580.25
...
```

## Testing

Run the full test suite:

```bash
pytest -v
```

Test coverage includes:
- Artist/work/quota insertion and UPSERT logic
- Transaction data loading
- Royalty calculation (transaction-level and aggregated)
- Report formatting

**Run specific test file:**

```bash
pytest tests/test_etl.py -v
pytest tests/test_queries.py -v
```

**Run with coverage:**

```bash
pytest --cov=etl --cov=db --cov-report=html
```

## Data Model

### Artists

Each artist has:
- `name` – Unique identifier
- `royalty_pct` – Percentage of net revenue earned (0.08–0.18)
- `advance_paid` – Total advance payment already made
- `advance_pending` – Advance amount available for recoupment
- `is_front_artist` – Whether this is a solo artist or backing performer
- `main_genre` – Primary genre classification
- `work_type` – Release type (Album, Single, EP)

### Works

Each track/release has:
- `title` – Work title
- `artist_id` – Primary artist (always receives a quota)
- `quotas` – List of artist splits (sum must equal 100%)
  - Example: `[{"artist_id": 1, "quota_pct": 70}, {"artist_id": 2, "quota_pct": 30}]`
- `genre`, `bpm`, `key`, `duration_seconds` – Metadata
- `iswc` – International Standard Musical Work Code
- `release_date` – ISO format date

### Transactions

Each streaming/purchase record has:
- `work_id` – Which track earned revenue
- `period` – Month of earnings (YYYY-MM-01 format)
- `gross_rev` – Revenue before platform/distribution costs (USD)
- `platform_fee` – Optional platform deduction (not yet used in royalty calc)
- `distr_cost` – Optional distribution cost (not yet used in royalty calc)
- `source` – Platform (Spotify, Apple Music, etc.)
- `territory` – Country code where transaction occurred
- `streaming_source` – Type (Stream, Purchase, etc.)

### Royalty Calculation

**Net Revenue** = Gross Revenue − Platform Fee − Distribution Cost

**Artist Royalty** = Net Revenue × Artist's Royalty % × Their Quota %

**Advance Recoupment** = min(Total Earned, Advance Pending)

**Net Royalty** = Total Earned − Advance Recoupment

## Logging

All operations are logged to both console and `logs/etl.log` via the `@log_operation` decorator:

```python
@log_operation
def load_artists(conn, loaded_at):
    # Automatically logs entry, exit, and errors
    ...
```

## Error Handling

The system validates data integrity at load time:
- Missing artist references → Warning + skip transaction
- Missing work title → Warning + skip transaction
- Invalid date formats → Exception logged and raised
- Database constraint violations → Automatic UPSERT (ON CONFLICT)

## Next Steps (TIER 2)

- [ ] Implement advance recoupment UI
- [ ] Add CI/CD pipeline (GitHub Actions)
- [ ] Build REST API endpoints
- [ ] Add multi-currency support
- [ ] Dashboard and analytics

## License

Proprietary – Phobos Records

## Support

For issues or questions, check the logs in `logs/etl.log` or review the data consistency validation in the test suite.
