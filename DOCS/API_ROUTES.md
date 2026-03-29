# Phobos Records API Routes

Le seguenti route sono necessarie per il backend. Le carte hai due opzioni principali:
1. **REST API** - endpoint HTTP tradizionali
2. **GraphQL** - single endpoint con query/mutation

## Option 1: REST API Endpoints

### Artists (Artisti)
```
GET    /api/artists               # Lista artisti con paginazione
POST   /api/artists               # Crea nuovo artista
GET    /api/artists/:id           # Dettaglio artista
PUT    /api/artists/:id           # Modifica artista
DELETE /api/artists/:id           # Cancella artista
```

**Artist Model:**
```json
{
  "id": integer,
  "artist_name": string,
  "royalty_pct": float (0.0-1.0),
  "advanced_paid": float,
  "advance_pending": float,
  "is_front_artist": boolean,
  "artist_image": string (URL),
  "main_genre": string,
  "work_type": string (Album|EP|Single),
  "created_at": timestamp,
  "updated_at": timestamp
}
```

### Works (Brani/Album)
```
GET    /api/works                 # Lista works con paginazione
POST   /api/works                 # Crea nuovo work
GET    /api/works/:id             # Dettaglio work
PUT    /api/works/:id             # Modifica work
DELETE /api/works/:id             # Cancella work
```

**Work Model:**
```json
{
  "id": integer,
  "title": string,
  "artist_id": integer (FK to artists),
  "secondary_artists_id": array[integer],
  "quotas": array[{
    "artist_id": integer,
    "quota_pct": float (0.0-1.0)
  }],
  "work_cover": string (URL),
  "release_date": date,
  "iswc": string,
  "genre": array[string],
  "duration_seconds": integer,
  "key": string,
  "bpm": integer,
  "created_at": timestamp,
  "updated_at": timestamp
}
```

## Frontend Integration

Il frontend attualmente:
- Fa POST alle API con `console.log` (pronto per integrare fetch/axios)
- Mostra alert per il feedback
- Non persiste i dati (ricaricando la pagina non restano)

### Punti di integrazione (artists.html):
```javascript
// Riga ~230: POST /api/artists
const formData = {
  name: artistName,
  royalty_pct: royaltyPct,
  advanced_paid: advancedPaid,
  loaded_at: timestamp
}
```

### Punti di integrazione (works.html):
```javascript
// Riga ~260: POST /api/works
const workData = {
  artist_id: artistId,
  title: title,
  loaded_at: timestamp
}
```

## Priority

### Must Have (Fase 1)
- [x] GET /api/artists (lista)
- [x] POST /api/artists (create)
- [x] GET /api/works (lista)
- [x] POST /api/works (create)

### Nice to Have (Fase 2)
- [ ] PUT /api/artists/:id (update)
- [ ] DELETE /api/artists/:id (delete)
- [ ] PUT /api/works/:id (update)
- [ ] DELETE /api/works/:id (delete)
- [ ] Filtri/ricerca per genere, artista, etc.
- [ ] Paginazione effettiva (ora è fittizia)

## Stack Consigliato

### Backend
- **Node.js + Express** - REST tradizionale, facile da mettere su
- **Python + FastAPI** - Moderno, documentazione Swagger automatica
- **Go** - Performance, single binary
- **Rust** - Type-safe, performance ottimale

### Database
- **PostgreSQL** - SQL relazionale, buono per questi dati
- **MongoDB** - NoSQL, più flessibile per schema
- **SQLite** - Sviluppo rapido, buono per prototipo

### ORM/Query Builder
- **Prisma** (Node.js)
- **SQLAlchemy** (Python)
- **Diesel** (Rust)
- **GORM** (Go)
