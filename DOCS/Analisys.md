# Phobos Records — Analisi Contestualizzata per Recruiter

## 👀 Cosa Vede un Recruiter Tecnico (Aprenso i File .py)

### db.py — Primo Impatto

```sql
CREATE TABLE IF NOT EXISTS artists (
    artist_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    royalty_pct NUMERIC(5,2) NOT NULL,
    advanced_paid NUMERIC(10,2) NOT NULL,
    advance_pending NUMERIC(10,2) NOT NULL,
    is_front_artist BOOLEAN NOT NULL,
    loaded_at TIMESTAMP NOT NULL
)
```

**✅ Cosa pensa il recruiter:**
- "Sa usare PRIMARY KEY, FOREIGN KEY"
- "Usa NUMERIC per i decimali (non FLOAT) — buona pratica"
- "Ha aggiunto loaded_at per audit trail"
- "Conosce ON CONFLICT DO UPDATE (idempotenza)"

**⚠️ Cosa manca (e un recruiter del settore nota):**
- `artist_image` — Come identifichi visivamente l'artista?
- `main_genre` — Un artista senza genere? Nel 2026?
- `work_type` — Non distingui ALBUM da SINGOLO?
- `is_front_artist` c'è ma è `NOT NULL` senza DEFAULT — crasha se non lo passi

---

### etl_in.py — Secondo Impatto

```python
def insert_artist(conn, name, royalty_pct, advanced_paid, loaded_at):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO artists (...)
        ON CONFLICT (name) DO UPDATE SET ...
    """)
```

**✅ Cosa pensa il recruiter:**
- "Separa le funzioni (insert_artist, insert_work, insert_transaction)"
- "Usa parameterized query (no SQL injection)"
- "Gestisce i conflitti in modo elegante"
- "Il flusso è chiaro: artists → works → transactions"

**⚠️ Cosa manca (e un recruiter del settore nota):**
- Legge solo `works.json` — dove sono `artists.json` e `transactions.csv`?
- Prende solo `data['artists'][0]` — **un solo artista**? Una label reale ne ha decine
- Nessun controllo se il JSON ha la struttura giusta (try/except)
- Nessun logging — se fallisce, sai solo che fallisce

---

### etl_out.py — Terzo Impatto

```sql
SELECT
    a.name,
    a.royalty_pct,
    w.title,
    t.gross_rev - t.platform_fee - t.distr_cost AS net_rev,
    (t.gross_rev - t.platform_fee - t.distr_cost) * a.royalty_pct AS royalty
FROM transactions t
JOIN works w ON t.work_id = w.work_id
JOIN artists a ON w.artist_id = a.artist_id
```

**✅ Cosa pensa il recruiter:**
- "Sa fare JOIN tra 3 tabelle"
- "La formula di calcolo è corretta (lordo - fees × royalty%)"
- "Restituisce dict invece di tuple — più leggibile"

**⚠️ Cosa manca (e un recruiter del settore nota):**
- **Nessuna gestione degli advance** — il cliente ha detto "tolgi l'anticipo una volta"
- **Nessuna quota per secondary artists** — le collaborazioni non esistono?
- **Nessuna distinzione revenue source** — streaming vs live vs merch sono tutti uguali?
- **Nessuna aggregazione** — solo righe singole, non totali per artista/mese

---

## 🎵 COSA MANCA NEL CONTESTO DISCOGRAFICO

### 1. Revenue Sources Multiple (REQS.md: "TUTTE")

**Cosa c'è ora:**
```python
source TEXT NOT NULL  # "spotify", "apple_music"
```

**Cosa serve in una label reale:**
```
- Streaming (Spotify, Apple Music, Amazon Music)
- Download (iTunes, Beatport)
- Live (concerti, festival)
- Merch (vendita fisica, online)
- Sync (TV, film, pubblicità)
- Radio (airplay, SIAE)
- YouTube (Content ID)
```

**Perché importa:** Ogni source ha:
- Fee diverse (Spotify ~30%, live ~80% all'artista)
- Timing diversi (streaming mensile, live post-evento)
- Split diversi (merch 50/50, streaming a percentuale)

---

### 2. Split Multi-Artista (Tabella `quotas` mancante)

**Scenario reale:**
```
"Event Horizon" — Lyra Void feat. Kraken
- Lyra Void: 70%
- Kraken: 30%
```

**Cosa c'è ora:**
```sql
works (
    artist_id INTEGER  -- UN SOLO ARTISTA
)
```

**Cosa serve:**
```sql
quotas (
    work_id INTEGER,
    artist_id INTEGER,
    quota_pct NUMERIC(5,2)  -- 0.70, 0.30
)
```

**Perché importa:** Nel 2026, **il 60%+ delle release ha featured artist**. Ignorarlo significa non gestire metà del catalogo.

---

### 3. Advance Management (REQS.md: "anticipo artisti")

**Scenario reale:**
```
Artista firma con la label → €10.000 advance
Primo mese: €2.000 royalty → NON PAGATI (recupero advance)
Secondo mese: €3.000 royalty → NON PAGATI (recupero advance)
Terzo mese: €4.000 royalty → €1.000 PAGATI (advance recuperato)
```

**Cosa c'è ora:**
```sql
artists (
    advanced_paid NUMERIC(10,2),
    advance_pending NUMERIC(10,2)
)
```

**Cosa manca:**
- Logica di calcolo: `IF advance_pending > 0 THEN royalty -= advance_pending`
- Tracking: quanto advance è stato recuperato?
- Stato: `is_artist_paid BOOLEAN` per transazione

**Perché importa:** Gli advance sono **il principale meccanismo di rischio** per una label. Non tracciarli significa non sapere se stai guadagnando o perdendo.

---

### 4. Metadata Musicali (works — campi mancanti)

**Cosa c'è ora:**
```sql
works (
    title TEXT,
    artist_id INTEGER
)
```

**Cosa serve in una label reale:**
```sql
works (
    title TEXT,
    artist_id INTEGER,
    secondary_artists TEXT[],     -- Featured artists
    work_cover TEXT,              -- URL copertina
    genre TEXT[],                 -- ["Electronic", "Techno"]
    bpm INT,                      -- 128
    iswc TEXT,                    -- Codice identificativo internazionale
    key TEXT,                     -- "A minor"
    work_type TEXT                -- "album", "single", "ep"
)
```

**Perché importa:**
- **ISWC** è obbligatorio per royalty collection (SIAE, ASCAP, BMI)
- **Genre** serve per reporting e marketing
- **BPM e Key** servono per playlist e DJ
- **work_type** cambia la strategia di release

---

### 5. Territory e Platform (transactions — campi mancanti)

**Cosa c'è ora:**
```sql
transactions (
    source TEXT,         -- "spotify"
    gross_rev NUMERIC
)
```

**Cosa serve:**
```sql
transactions (
    platform TEXT,       -- "spotify"
    territory CHAR(2),   -- "IT", "US", "DE"
    purchase_month TEXT, -- "2026-01"
    is_artist_paid BOOLEAN
)
```

**Perché importa:**
- **Territory**: Le royalty cambiano per paese (USA pagano di più dell'Europa)
- **Purchase month**: Utile per report mensili separati dal periodo di competenza
- **is_artist_paid**: Per sapere quali transazioni sono già state processate

---

### 6. Formato Dati di Input (REQS.md: transaction.csv)

**Cosa c'è ora:**
```json
{
  "artists": [{
    "works": [{
      "transactions": [...]
    }]
  }]
}
```

**Cosa chiede il cliente:**
```csv
INSERITO|SEGNALATO|MESE|STORE|ARTISTA|TITOLO|QUANTITÀ|TIPO|SPLIT|PAESE|GUADAGNI
2026-01-15|2026-02-18|2026-01|Spotify|Kraken|Alluminio|127|Stream|50%|IT|53099
```

**Perché importa:** Le label **ricevono report CSV dalle piattaforme**, non JSON. Il tuo ETL deve leggere il formato reale, non un formato inventato.

---

## 📊 GIUDIZIO PER UN RECRUITER DEL SETTORE

| Aspetto | Voto | Note |
|---------|------|------|
| **SQL Base** | 8/10 | JOIN, FK, NUMERIC corretti |
| **Python Base** | 7/10 | Funzioni separate, JSON parsing |
| **ETL Pattern** | 6/10 | Input/output separati, ma limitato |
| **Dominio Musicale** | 3/10 | Manca il 70% dei campi reali |
| **Scalabilità** | 4/10 | 1 artista, 1 opera, 1 transazione |
| **Error Handling** | 2/10 | Assente |
| **Logging** | 0/10 | Assente |
| **Test** | 1/10 | Quasi vuoto |

**Media: 3.9/10 — Junior con potenziale, ma non pronto per produzione**

---

## 🎯 COSA CAMBIEREBBE LA PERCEZIONE

### Con 2 ore di lavoro:
```sql
-- Aggiungi 5 campi a db.py
artist_image TEXT,
main_genre TEXT,
work_type TEXT,
iswc TEXT,
genre TEXT[]
```
**Recruiter pensa:** "Capisce il dominio musicale"

### Con 4 ore di lavoro:
```python
# Aggiungi try/except e logging
try:
    insert_artist(...)
except Exception as e:
    logging.error(f"Artist insert failed: {e}")
```
**Recruiter pensa:** "Scrives codice production-ready"

### Con 8 ore di lavoro:
```python
# Aggiungi tabella quotas
# Modifica etl_out per gestire split multipli
```
**Recruiter pensa:** "Ha lavorato in una label vera"

---

## 💡 CONCLUSIONE ONESTA

### Cosa il codice dice di te:
- ✅ Sai scrivere SQL corretto
- ✅ Conosci i pattern ETL base
- ✅ Sai strutturare codice Python leggibile
- ⚠️ Non hai mai gestito errori in produzione
- ⚠️ Non hai mai fatto logging o testing

### Cosa il codice NON dice (ma la documentazione sì):
- ✅ Sai pianificare prima di codificare
- ✅ Sai tracciare requisiti e task
- ✅ Sai documentare le decisioni


---

## 🔧 RACCOMANDAZIONI PRIORITARIE

### Se vuoi impressionare un recruiter **tecnico**:
1. Aggiungi error handling (try/except + logging)
2. Aggiungi test unitari (pytest)
3. Refactor con classi o dataclass


### Se vuoi impressionare **entrambi**:
1. Completa lo schema DB (2h)
2. Implementa 3-4 API base (6h)
3. Collega il frontend (3h)
4. Scrivi README pubblico (1h)

**Totale: ~12 ore per trasformare la percezione da 3/10 a 7/10**

---

*Analisi basata su: db.py, etl_in.py, etl_out.py, REQS.md, scrum.csv*
*Data: Febbraio 2026*
