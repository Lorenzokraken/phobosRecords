# Phobos Records — MVP Data Engineering

## Scope MVP (minimo sindacale)

- ✅ 1 artista → 1 opera → 1 transazione mensile
- ✅ JSON nested → ETL Python → PostgreSQL → print() royalty
- ✅ Frontend base (artisti, opere, dashboard)
- 🔄 API REST per calcolo revenue in tempo reale

---

## Entità core

## TABLES:

### 1. artists
   - artist_id           SERIAL          PK
   - name                TEXT            NOT NULL
   - royalty_pct         NUMERIC(5,2)    NOT NULL
   - advanced_paid       NUMERIC(10,2)   NOT NULL
   - advance_pending     NUMERIC(10,2)   NOT NULL
   - is_front_artist     BOOLEAN         NOT NULL
   - artist_image        TEXT            NOT NULL
   - main_genre          TEXT            NOT NULL
   - work_type           TEXT            NOT NULL
   - loaded_at           TIMESTAMP       NOT NULL

### 2. works
   - work_id             SERIAL          PK
   - artist_id           INTEGER         NOT NULL → artists.artist_id (FK)
   - title               TEXT            NOT NULL
   - secondary_artists   TEXT[]          NOT NULL
   - work_cover          TEXT            NOT NULL
   - genre               TEXT[]          NOT NULL
   - bpm                 INT
   - iswc                TEXT
   - key                 TEXT
   - loaded_at           TIMESTAMP       NOT NULL

### 3. transactions
   - transaction_id      SERIAL          PK
   - work_id             INTEGER         NOT NULL → works.work_id (FK)
   - period              DATE            NOT NULL
   - gross_rev           NUMERIC(10,2)   NOT NULL
   - source              TEXT            NOT NULL
   - platform_fee        NUMERIC(10,2)
   - distr_cost          NUMERIC(10,2)
   - is_artist_paid      BOOLEAN         NOT NULL
   - purchase_month      TEXT            NOT NULL
   - platform            TEXT            NOT NULL
   - territory           CHAR(2)         NOT NULL
   - loaded_at           TIMESTAMP       NOT NULL

### 4. quotas (NEW)
   - quota_id            SERIAL          PK
   - work_id             INTEGER         REFERENCES works(work_id)
   - artist_id           INTEGER         REFERENCES artists(artist_id)
   - quota_pct           NUMERIC(5,2)    NOT NULL
   - UNIQUE(work_id, artist_id)

---

## Flusso dati

```
artist.json → ETL → PostgreSQL
work.json   → ETL → PostgreSQL
transaction.csv → ETL → PostgreSQL
                    ↓
              API REST (calcolo in tempo reale)
```

---

## API Endpoint (MVP)

| Endpoint | Descrizione |
|----------|-------------|
| `/calculate_artist_revenue` | Revenue totale per artista |
| `/calculate_artist_monthly_revenue` | Revenue mensile per artista |
| `/calculate_work_revenue` | Revenue per opera |
| `/get_top_artist` | Artisti più performanti |
| `/tot_revenue` | Revenue complessivo |
| `/tot_unit_sold` | Unità vendute totali |
| `/get_works` | Lista opere |
| `/get_artist` | Lista artisti |
| `/create_work` | Crea nuova opera |
| `/create_artist` | Crea nuovo artista |

---

## Stack Tecnologico

- **Backend**: Python + FastAPI/Flask
- **Database**: PostgreSQL
- **ETL**: Python (JSON/CSV → DB)
- **Frontend**: HTML/CSS/JS (statico)
- **Logging**: File-based (api.log, etl.log)

---

## Struttura Progetto

```
phobos-mvp/
├── DOCS/
│   ├── PROJECT.md
│   ├── REQS.md
│   └── README.md
├── frontend/
│   ├── index.html
│   ├── artist.html
│   ├── works.html
│   └── src/
│       ├── Artists/
│       └── Albums/
├── db.py              ← schema tabelle
├── etl_input.py       ← JSON/CSV → DB
├── etl_output.py      ← query revenue
├── api.py             ← endpoint REST
├── artists.json
├── works.json
├── transactions.csv
└── requirements.txt
```

---

## Prossimi Step

1. **DB Schema v1.2**: Aggiornare tabelle con nuovi campi
2. **ETL**: Supporto per artist.json, work.json, transaction.csv
3. **API**: Implementare endpoint base con FastAPI
4. **Logging**: Sistema di logging per API e ETL
5. **Test**: Validare calcolo netto/lordo + advance

---

## Note Importanti

- **Calcolo royalty**: Lordo → Netto - Advance già pagati
- **Revenue sources**: Streaming, Live, Merch, Sync
- **Immagini**: Artisti e opere con URL esterni
- **Frequenza**: Calcolo real-time all'insert (no batch settimanale)







Test API endpoint	❌ Mancante
CI/CD Pipeline	❌ Mancante
NICE TO HAVE
Task	Stato
Pagination dinamica	❌ (statica)
Form artisti con API	✅ Fatto — modal + POST /api/artists + upload immagine
Form opere con API	✅ Fatto — modal + POST /api/works + upload cover
Dashboard con API	❌

Il pattern più semplice da studiare è GET /tot_revenue in src/routes.py:212:


@router.get("/tot_revenue")
def tot_revenue(year: Optional[int] = Query(None), db=Depends(get_db)):
    logger.info(f"GET /tot_revenue - year={year}")   # ← log ingresso con parametro
    cur = db.cursor()
    where = ("WHERE EXTRACT(YEAR FROM period) = %s" if year is not None else "")
    params = [year] if year is not None else []
    cur.execute(f"SELECT COALESCE(SUM(gross_rev), 0) FROM transactions {where}", params)
    total = float(cur.fetchone()[0])
    cur.close()
    return {"total_revenue": total, "year": year or "all"}
Mostra tutto il pattern API in ~10 righe: parametro opzionale, query SQL, log, risposta JSON. Niente errori da gestire perché non può fallire su dati vuoti (COALESCE).