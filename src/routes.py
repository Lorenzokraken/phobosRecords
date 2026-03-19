import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .db import get_db

router = APIRouter()
logger = logging.getLogger("phobos.api")


# --- Pydantic Models ---

class ArtistCreate(BaseModel):
    artist_name: str
    royalty_pct: float
    advanced_paid: float = 0.0
    advance_pending: float = 0.0
    is_front_artist: bool = False
    artist_image: str = ""
    main_genre: str = ""
    work_type: str = "Album"


class WorkCreate(BaseModel):
    title: str
    artist_id: int
    secondary_artists_id: list = []
    work_cover: str = ""
    release_date: str = ""
    iswc: str = ""
    genre: list = []
    duration_seconds: int = 0
    key: str = ""
    bpm: int = 0


# --- Revenue Routes ---

@router.get("/calculate_artist_revenue")
def calculate_artist_revenue(
    artist_id: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Revenue netta per artista (gross_rev * royalty_pct), con filtri opzionali."""
    logger.info(f"GET /calculate_artist_revenue - artist_id={artist_id} year={year}")
    cur = db.cursor()
    conditions = []
    params = []

    if artist_id is not None:
        conditions.append("a.artist_id = %s")
        params.append(artist_id)
    if year is not None:
        conditions.append("EXTRACT(YEAR FROM t.period) = %s")
        params.append(year)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    cur.execute(f"""
        SELECT a.artist_id, a.name,
               COALESCE(SUM(t.gross_rev), 0) * a.royalty_pct AS revenue
        FROM artists a
        LEFT JOIN works w ON a.artist_id = w.artist_id
        LEFT JOIN transactions t ON w.work_id = t.work_id
        {where}
        GROUP BY a.artist_id, a.name, a.royalty_pct
        ORDER BY revenue DESC
    """, params)

    rows = cur.fetchall()
    cur.close()
    logger.info(f"Returning revenue for {len(rows)} artists")
    return {
        "revenues": [
            {"artist_id": r[0], "artist_name": r[1], "revenue": float(r[2])}
            for r in rows
        ]
    }


@router.get("/calculate_artist_monthly_revenue")
def calculate_artist_monthly_revenue(
    artist_id: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Revenue netta per artista per mese."""
    logger.info(f"GET /calculate_artist_monthly_revenue - artist_id={artist_id}")
    cur = db.cursor()
    where = "WHERE t.purchase_month IS NOT NULL"
    params = []

    if artist_id is not None:
        where += " AND a.artist_id = %s"
        params.append(artist_id)

    cur.execute(f"""
        SELECT a.artist_id, a.name, t.purchase_month,
               COALESCE(SUM(t.gross_rev), 0) * a.royalty_pct AS revenue
        FROM artists a
        LEFT JOIN works w ON a.artist_id = w.artist_id
        LEFT JOIN transactions t ON w.work_id = t.work_id
        {where}
        GROUP BY a.artist_id, a.name, a.royalty_pct, t.purchase_month
        ORDER BY a.artist_id, t.purchase_month
    """, params)

    rows = cur.fetchall()
    cur.close()
    return {
        "revenues": [
            {"artist_id": r[0], "artist_name": r[1], "month": r[2], "revenue": float(r[3])}
            for r in rows
        ]
    }


@router.get("/calculate_work_revenue")
def calculate_work_revenue(
    work_id: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Revenue lorda per opera, con filtro opzionale per work_id."""
    logger.info(f"GET /calculate_work_revenue - work_id={work_id}")
    cur = db.cursor()
    where = ("WHERE w.work_id = %s" if work_id is not None else "")
    params = [work_id] if work_id is not None else []

    cur.execute(f"""
        SELECT w.work_id, w.title, a.name AS artist_name,
               COALESCE(SUM(t.gross_rev), 0) AS gross_revenue
        FROM works w
        JOIN artists a ON w.artist_id = a.artist_id
        LEFT JOIN transactions t ON w.work_id = t.work_id
        {where}
        GROUP BY w.work_id, w.title, a.name
        ORDER BY gross_revenue DESC
    """, params)

    rows = cur.fetchall()
    cur.close()
    return {
        "revenues": [
            {"work_id": r[0], "title": r[1], "artist_name": r[2], "gross_revenue": float(r[3])}
            for r in rows
        ]
    }


@router.get("/calculate_work_monthly_revenue")
def calculate_work_monthly_revenue(
    work_id: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Revenue lorda per opera per mese."""
    cur = db.cursor()
    where = "WHERE t.purchase_month IS NOT NULL"
    params = []

    if work_id is not None:
        where += " AND w.work_id = %s"
        params.append(work_id)

    cur.execute(f"""
        SELECT w.work_id, w.title, t.purchase_month,
               COALESCE(SUM(t.gross_rev), 0) AS revenue
        FROM works w
        LEFT JOIN transactions t ON w.work_id = t.work_id
        {where}
        GROUP BY w.work_id, w.title, t.purchase_month
        ORDER BY w.work_id, t.purchase_month
    """, params)

    rows = cur.fetchall()
    cur.close()
    return {
        "revenues": [
            {"work_id": r[0], "title": r[1], "month": r[2], "revenue": float(r[3])}
            for r in rows
        ]
    }


# --- Top Artist ---

@router.get("/get_top_artist")
def get_top_artist(
    year: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Artista con la revenue lorda più alta."""
    logger.info(f"GET /get_top_artist - year={year}")
    cur = db.cursor()
    where = ("WHERE EXTRACT(YEAR FROM t.period) = %s" if year is not None else "")
    params = [year] if year is not None else []

    cur.execute(f"""
        SELECT a.artist_id, a.name, a.main_genre,
               COALESCE(SUM(t.gross_rev), 0) AS total_revenue
        FROM artists a
        LEFT JOIN works w ON a.artist_id = w.artist_id
        LEFT JOIN transactions t ON w.work_id = t.work_id
        {where}
        GROUP BY a.artist_id, a.name, a.main_genre
        ORDER BY total_revenue DESC
        LIMIT 1
    """, params)

    row = cur.fetchone()
    cur.close()
    if not row:
        raise HTTPException(status_code=404, detail="No artists found")
    return {"artist_id": row[0], "artist_name": row[1], "main_genre": row[2], "total_revenue": float(row[3])}


# --- Aggregates ---

@router.get("/tot_revenue")
def tot_revenue(
    year: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Revenue lorda totale, con filtro opzionale per anno."""
    logger.info(f"GET /tot_revenue - year={year}")
    cur = db.cursor()
    where = ("WHERE EXTRACT(YEAR FROM period) = %s" if year is not None else "")
    params = [year] if year is not None else []

    cur.execute(f"SELECT COALESCE(SUM(gross_rev), 0) FROM transactions {where}", params)
    total = float(cur.fetchone()[0])
    cur.close()
    return {"total_revenue": total, "year": year or "all"}


@router.get("/tot_unit_sold")
def tot_unit_sold(
    year: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Numero totale di transazioni (unità vendute), con filtro opzionale per anno."""
    logger.info(f"GET /tot_unit_sold - year={year}")
    cur = db.cursor()
    where = ("WHERE EXTRACT(YEAR FROM period) = %s" if year is not None else "")
    params = [year] if year is not None else []

    cur.execute(f"SELECT COUNT(*) FROM transactions {where}", params)
    total = cur.fetchone()[0]
    cur.close()
    return {"total_units": total, "year": year or "all"}


@router.get("/total_yearly_listeners")
def total_yearly_listeners(db=Depends(get_db)):
    """Conteggio transazioni per anno (proxy per listeners)."""
    cur = db.cursor()
    cur.execute("""
        SELECT EXTRACT(YEAR FROM period)::int AS year, COUNT(*) AS listeners
        FROM transactions
        GROUP BY year
        ORDER BY year
    """)
    rows = cur.fetchall()
    cur.close()
    return {"listeners": [{"year": r[0], "count": r[1]} for r in rows]}


# --- Works & Artists ---

@router.get("/recent_releases")
def recent_releases(
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db)
):
    """Ultime opere rilasciate, ordinate per release_date."""
    cur = db.cursor()
    cur.execute("""
        SELECT w.work_id, w.title, a.name AS artist_name,
               w.release_date, w.genre, w.work_cover
        FROM works w
        JOIN artists a ON w.artist_id = a.artist_id
        ORDER BY w.release_date DESC
        LIMIT %s
    """, [limit])
    rows = cur.fetchall()
    cur.close()
    return {
        "releases": [
            {
                "work_id": r[0], "title": r[1], "artist_name": r[2],
                "release_date": str(r[3]), "genre": r[4], "work_cover": r[5]
            }
            for r in rows
        ]
    }


@router.get("/get_works")
def get_works(
    artist_id: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Lista opere, con filtro opzionale per artista."""
    cur = db.cursor()
    where = ("WHERE w.artist_id = %s" if artist_id is not None else "")
    params = [artist_id] if artist_id is not None else []

    cur.execute(f"""
        SELECT w.work_id, w.title, a.name AS artist_name,
               w.genre, w.bpm, w.song_key, w.release_date, w.duration
        FROM works w
        JOIN artists a ON w.artist_id = a.artist_id
        {where}
        ORDER BY w.release_date DESC
    """, params)

    rows = cur.fetchall()
    cur.close()
    return {
        "works": [
            {
                "work_id": r[0], "title": r[1], "artist_name": r[2],
                "genre": r[3], "bpm": r[4], "key": r[5],
                "release_date": str(r[6]), "duration": r[7]
            }
            for r in rows
        ]
    }


@router.get("/get_artist")
def get_artist(
    artist_id: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Dettaglio artista o lista tutti gli artisti."""
    cur = db.cursor()
    where = ("WHERE artist_id = %s" if artist_id is not None else "")
    params = [artist_id] if artist_id is not None else []

    cur.execute(f"""
        SELECT artist_id, name, royalty_pct, main_genre, work_type,
               is_front_artist, advance_paid, advance_pending
        FROM artists
        {where}
        ORDER BY name
    """, params)

    rows = cur.fetchall()
    cur.close()

    artists = [
        {
            "artist_id": r[0], "name": r[1], "royalty_pct": float(r[2]),
            "main_genre": r[3], "work_type": r[4], "is_front_artist": r[5],
            "advance_paid": float(r[6]), "advance_pending": float(r[7])
        }
        for r in rows
    ]

    if artist_id is not None and not artists:
        raise HTTPException(status_code=404, detail="Artist not found")

    return {"artists": artists}


# --- Create Routes ---

@router.post("/create_artist")
def create_artist(artist: ArtistCreate, db=Depends(get_db)):
    """Crea un nuovo artista nel database."""
    logger.info(f"POST /create_artist - name={artist.artist_name}")
    cur = db.cursor()
    try:
        cur.execute("""
            INSERT INTO artists (name, royalty_pct, advance_paid, advance_pending,
                                 is_front_artist, artist_image, main_genre, work_type, loaded_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING artist_id
        """, (
            artist.artist_name, artist.royalty_pct, artist.advanced_paid,
            artist.advance_pending, artist.is_front_artist, artist.artist_image,
            artist.main_genre, artist.work_type, datetime.now()
        ))
        artist_id = cur.fetchone()[0]
        db.commit()
        cur.close()
        return {"status": "success", "artist_id": artist_id, "artist_name": artist.artist_name}
    except Exception as e:
        db.rollback()
        cur.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revenue_by_platform")
def revenue_by_platform(
    year: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Revenue lorda per piattaforma (Spotify, Deezer, ecc.)."""
    logger.info(f"GET /revenue_by_platform - year={year}")
    cur = db.cursor()
    where = ("WHERE EXTRACT(YEAR FROM period) = %s" if year is not None else "")
    params = [year] if year is not None else []
    cur.execute(f"""
        SELECT platform, COALESCE(SUM(gross_rev), 0) AS revenue
        FROM transactions
        {where}
        GROUP BY platform
        ORDER BY revenue DESC
    """, params)
    rows = cur.fetchall()
    cur.close()
    return {"platforms": [{"platform": r[0], "revenue": float(r[1])} for r in rows]}


@router.get("/top_works")
def top_works(
    limit: int = Query(5, ge=1, le=20),
    year: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Top opere per revenue lorda."""
    logger.info(f"GET /top_works - limit={limit} year={year}")
    cur = db.cursor()
    where = ("WHERE EXTRACT(YEAR FROM t.period) = %s" if year is not None else "")
    params = [year] if year is not None else []
    cur.execute(f"""
        SELECT w.work_id, w.title, a.name AS artist_name,
               COALESCE(SUM(t.gross_rev), 0) AS gross_revenue
        FROM works w
        JOIN artists a ON w.artist_id = a.artist_id
        LEFT JOIN transactions t ON w.work_id = t.work_id
        {where}
        GROUP BY w.work_id, w.title, a.name
        ORDER BY gross_revenue DESC
        LIMIT %s
    """, params + [limit])
    rows = cur.fetchall()
    cur.close()
    return {"works": [{"work_id": r[0], "title": r[1], "artist_name": r[2], "gross_revenue": float(r[3])} for r in rows]}


@router.get("/monthly_trend")
def monthly_trend(db=Depends(get_db)):
    """Trend mensile totale revenue con variazione percentuale."""
    logger.info("GET /monthly_trend")
    cur = db.cursor()
    cur.execute("""
        SELECT purchase_month, COALESCE(SUM(gross_rev), 0) AS revenue
        FROM transactions
        WHERE purchase_month IS NOT NULL
        GROUP BY purchase_month
        ORDER BY purchase_month
    """)
    rows = cur.fetchall()
    cur.close()
    result = []
    for i, r in enumerate(rows):
        prev = float(rows[i-1][1]) if i > 0 else None
        curr = float(r[1])
        growth = round((curr - prev) / prev * 100, 2) if prev and prev > 0 else None
        result.append({"month": r[0], "revenue": curr, "growth_pct": growth})
    return {"trend": result}


@router.get("/revenue_by_genre")
def revenue_by_genre(
    year: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Revenue e unità vendute per genere (funnel)."""
    logger.info(f"GET /revenue_by_genre - year={year}")
    cur = db.cursor()
    where = ("WHERE EXTRACT(YEAR FROM t.period) = %s" if year is not None else "")
    params = [year] if year is not None else []
    cur.execute(f"""
        SELECT a.main_genre,
               COUNT(t.transaction_id) AS units_sold,
               COALESCE(SUM(t.gross_rev), 0) AS gross_revenue
        FROM artists a
        LEFT JOIN works w ON a.artist_id = w.artist_id
        LEFT JOIN transactions t ON w.work_id = t.work_id
        {where}
        GROUP BY a.main_genre
        ORDER BY gross_revenue DESC
    """, params)
    rows = cur.fetchall()
    cur.close()
    return {"genres": [{"genre": r[0], "units_sold": r[1], "gross_revenue": float(r[2])} for r in rows]}


@router.post("/create_work")
def create_work(work: WorkCreate, db=Depends(get_db)):
    """Crea una nuova opera nel database."""
    logger.info(f"POST /create_work - title={work.title} artist_id={work.artist_id}")
    cur = db.cursor()
    try:
        cur.execute("""
            INSERT INTO works (artist_id, title, secondary_artists_id, work_cover,
                               genre, bpm, iswc, song_key, release_date, duration, loaded_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING work_id
        """, (
            work.artist_id, work.title,
            ",".join(map(str, work.secondary_artists_id)),
            work.work_cover, work.genre, work.bpm, work.iswc,
            work.key, work.release_date or None,
            work.duration_seconds, datetime.now()
        ))
        work_id = cur.fetchone()[0]
        db.commit()
        cur.close()
        return {"status": "success", "work_id": work_id, "title": work.title}
    except Exception as e:
        db.rollback()
        cur.close()
        raise HTTPException(status_code=500, detail=str(e))
