**Requisiti Cliente (Patrick - Phobos Records)**
- Revenue sources: TUTTE (streaming, live, merch, ...)
aggiungere a db nuovi campi (da ingegnerizzare db, avrete risposta in settimana)


- Output: split pagamento LORdo/NETTo + anticipo artisti
(si prende il costo lordo si calcola in base alla percentuale e va tolto l'anticipo una volta, probabilemnte serve fare due campi advance_paid e advance per distinguere i soldi già avanzati)


- Frequenza: WEEKLY (Consigliata giornaliera)
Orchestrazione settimanale delle revenue crea dei problemi di visualizzazione frontend, per la quantità di dati prevista è più sensato calcolare tutto al momento dell'insert dei dati, in modo da avere un feedback immediato sul frontend. per permettere questo considererei già da subito l'implementazione di un API.

iniziare implementare l'api



- Accessi: cofounder + manager artisti
Và aggiunta una login (Verificare la necessità piuttosto che fare un sistema chiuso, avete una parte che intendete esporre al pubblico?)


- Immagini del sito:
Il sito deve avere immagini linkate sia per gli artisti che per le opere


**Stima Vendor (Marco - DataFlow Solutions)**
- Deploy MVP: 4 settimane dalla kickoff
- Costo: 2.5-3k€
- Stack: low-cost (Python/PostgreSQL + mock JSON)
- Prossimo: proposal 48h + validazione Engineer

# MVP 

## IMPLEMENTAZIONE GIÀ REALIZZATA

### Database
- ✅ Creazione tabelle `artists`, `works`, e `transactions` in PostgreSQL


### ETL (Extract, Transform, Load)
- ✅ Script `etl_in.py` per l'inserimento dati da JSON al database
- ✅ Script `etl_out.py` per il calcolo delle royalty


### API
- ✅ Framework FastAPI implementato in `main.py`

### Frontend
- ✅ File `index.html` con layout responsive


# Endpoint API -13
/calculate_artist_revenue
/calculate_artist_monthly_revenue
/calculate_work_revenue
/calculate_work_monthly_revenue
/get_top_artist
/tot_revenue
/tot_unit_sold
/total_yearly_listeners
/recent_releases
/get_works
/get_artist
/create_work
/create_artist

# ETL
- cambiare calcolo netto/lordo

# TEST
api / etl

# LOGGING
api / etl

# DOCUMENTAZIONE
READ.md (DA FARE)