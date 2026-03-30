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


# --- Aggregation Refresh ---

@router.post("/refresh_aggregates")
def refresh_aggregates(db=Depends(get_db)):
    """Full refresh of aggregated_royalties summary table."""
    logger.info("POST /refresh_aggregates")
    from .db import refresh_aggregated_royalties
    rows = refresh_aggregated_royalties()
    logger.info(f"Aggregated royalties refreshed: {rows} rows")
    return {"status": "success", "rows_refreshed": rows, "refreshed_at": datetime.now().isoformat()}


# --- Revenue Routes (read from aggregated_royalties) ---

@router.get("/calculate_artist_revenue")
def calculate_artist_revenue(
    artist_id: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Revenue netta per artista, con filtri opzionali."""
    logger.info(f"GET /calculate_artist_revenue - artist_id={artist_id} year={year}")
    cur = db.cursor()
    conditions = []
    params = []

    if artist_id is not None:
        conditions.append("artist_id = %s")
        params.append(artist_id)
    if year is not None:
        conditions.append("period_year = %s")
        params.append(year)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    cur.execute(f"""
        SELECT artist_id, artist_name,
               SUM(gross_rev) * MAX(royalty_pct) AS revenue
        FROM aggregated_royalties
        {where}
        GROUP BY artist_id, artist_name
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
    conditions = []
    params = []

    if artist_id is not None:
        conditions.append("artist_id = %s")
        params.append(artist_id)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    cur.execute(f"""
        SELECT artist_id, artist_name, purchase_month,
               SUM(gross_rev) * MAX(royalty_pct) AS revenue
        FROM aggregated_royalties
        {where}
        GROUP BY artist_id, artist_name, purchase_month
        ORDER BY artist_id, purchase_month
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
    conditions = []
    params = []

    if work_id is not None:
        conditions.append("work_id = %s")
        params.append(work_id)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    cur.execute(f"""
        SELECT work_id, work_title, artist_name,
               SUM(gross_rev) AS gross_revenue
        FROM aggregated_royalties
        {where}
        GROUP BY work_id, work_title, artist_name
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
    conditions = []
    params = []

    if work_id is not None:
        conditions.append("work_id = %s")
        params.append(work_id)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    cur.execute(f"""
        SELECT work_id, work_title, purchase_month,
               SUM(gross_rev) AS revenue
        FROM aggregated_royalties
        {where}
        GROUP BY work_id, work_title, purchase_month
        ORDER BY work_id, purchase_month
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
    where = ("WHERE period_year = %s" if year is not None else "")
    params = [year] if year is not None else []

    cur.execute(f"""
        SELECT artist_id, artist_name, main_genre,
               SUM(gross_rev) AS total_revenue
        FROM aggregated_royalties
        {where}
        GROUP BY artist_id, artist_name, main_genre
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
    where = ("WHERE period_year = %s" if year is not None else "")
    params = [year] if year is not None else []

    cur.execute(f"SELECT COALESCE(SUM(gross_rev), 0) FROM aggregated_royalties {where}", params)
    total = float(cur.fetchone()[0])
    cur.close()
    return {"total_revenue": total, "year": year or "all"}


@router.get("/tot_unit_sold")
def tot_unit_sold(
    year: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Numero totale di unità vendute, con filtro opzionale per anno."""
    logger.info(f"GET /tot_unit_sold - year={year}")
    cur = db.cursor()
    where = ("WHERE period_year = %s" if year is not None else "")
    params = [year] if year is not None else []

    cur.execute(f"SELECT COALESCE(SUM(units_sold), 0) FROM aggregated_royalties {where}", params)
    total = int(cur.fetchone()[0])
    cur.close()
    return {"total_units": total, "year": year or "all"}


@router.get("/total_yearly_listeners")
def total_yearly_listeners(db=Depends(get_db)):
    """Conteggio unità vendute per anno (proxy per listeners)."""
    cur = db.cursor()
    cur.execute("""
        SELECT period_year, SUM(units_sold) AS listeners
        FROM aggregated_royalties
        GROUP BY period_year
        ORDER BY period_year
    """)
    rows = cur.fetchall()
    cur.close()
    return {"listeners": [{"year": r[0], "count": int(r[1])} for r in rows]}


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
    """Revenue lorda per piattaforma."""
    logger.info(f"GET /revenue_by_platform - year={year}")
    cur = db.cursor()
    where = ("WHERE period_year = %s" if year is not None else "")
    params = [year] if year is not None else []
    cur.execute(f"""
        SELECT platform, COALESCE(SUM(gross_rev), 0) AS revenue
        FROM aggregated_royalties
        {where}
        GROUP BY platform
        ORDER BY revenue DESC
    """, params)
    rows = cur.fetchall()
    cur.close()
    return {"platforms": [{"platform": r[0], "revenue": float(r[1])} for r in rows]}


@router.get("/revenue_by_platform_detail")
def revenue_by_platform_detail(db=Depends(get_db)):
    """Revenue per piattaforma con breakdown per artista."""
    cur = db.cursor()
    cur.execute("""
        SELECT platform, artist_name, COALESCE(SUM(gross_rev), 0) AS revenue
        FROM aggregated_royalties
        GROUP BY platform, artist_name
        ORDER BY platform, revenue DESC
    """)
    rows = cur.fetchall()
    cur.close()
    return {"detail": [{"platform": r[0], "artist_name": r[1], "revenue": float(r[2])} for r in rows]}


@router.get("/top_works")
def top_works(
    limit: int = Query(5, ge=1, le=20),
    year: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Top opere per revenue lorda."""
    logger.info(f"GET /top_works - limit={limit} year={year}")
    cur = db.cursor()
    where = ("WHERE period_year = %s" if year is not None else "")
    params = [year] if year is not None else []
    cur.execute(f"""
        SELECT work_id, work_title, artist_name,
               SUM(gross_rev) AS gross_revenue
        FROM aggregated_royalties
        {where}
        GROUP BY work_id, work_title, artist_name
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
        FROM aggregated_royalties
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
    """Revenue e unità vendute per genere."""
    logger.info(f"GET /revenue_by_genre - year={year}")
    cur = db.cursor()
    where = ("WHERE period_year = %s" if year is not None else "")
    params = [year] if year is not None else []
    cur.execute(f"""
        SELECT main_genre,
               SUM(units_sold) AS units_sold,
               COALESCE(SUM(gross_rev), 0) AS gross_revenue
        FROM aggregated_royalties
        {where}
        GROUP BY main_genre
        ORDER BY gross_revenue DESC
    """, params)
    rows = cur.fetchall()
    cur.close()
    return {"genres": [{"genre": r[0], "units_sold": int(r[1]), "gross_revenue": float(r[2])} for r in rows]}


@router.get("/api/revenue/mtd")
def revenue_mtd(db=Depends(get_db)):
    """Revenue mese corrente vs mese precedente."""
    logger.info("GET /api/revenue/mtd")
    cur = db.cursor()
    cur.execute("""
        WITH monthly AS (
            SELECT
                DATE_TRUNC('month', purchase_month) AS mo,
                COALESCE(SUM(gross_rev), 0) AS rev
            FROM aggregated_royalties
            GROUP BY 1
            ORDER BY 1 DESC
            LIMIT 2
        )
        SELECT mo, rev FROM monthly ORDER BY mo DESC
    """)
    rows = cur.fetchall()
    cur.close()
    if not rows:
        return {"value": 0, "vs_last_month_pct": None}
    current = float(rows[0][1])
    previous = float(rows[1][1]) if len(rows) > 1 else None
    pct = round((current - previous) / previous * 100, 1) if previous and previous > 0 else None
    return {"value": current, "vs_last_month_pct": pct, "month": rows[0][0].strftime("%B %Y") if rows[0][0] else None}


@router.get("/api/top-work")
def top_work(db=Depends(get_db)):
    """Opera con la revenue lorda più alta nel mese corrente."""
    logger.info("GET /api/top-work")
    cur = db.cursor()
    cur.execute("""
        SELECT work_id, work_title, artist_name, SUM(gross_rev) AS revenue
        FROM aggregated_royalties
        WHERE DATE_TRUNC('month', purchase_month) = DATE_TRUNC('month', (
            SELECT MAX(purchase_month) FROM aggregated_royalties
        ))
        GROUP BY work_id, work_title, artist_name
        ORDER BY revenue DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    cur.close()
    if not row:
        raise HTTPException(status_code=404, detail="No works found")
    return {"work_id": row[0], "title": row[1], "artist": row[2], "revenue": float(row[3])}


@router.get("/api/top-artist-mtd")
def top_artist_mtd(db=Depends(get_db)):
    """Artista con la revenue lorda più alta nel mese corrente."""
    logger.info("GET /api/top-artist-mtd")
    cur = db.cursor()
    cur.execute("""
        SELECT artist_id, artist_name, main_genre, SUM(gross_rev) AS revenue
        FROM aggregated_royalties
        WHERE DATE_TRUNC('month', purchase_month) = DATE_TRUNC('month', (
            SELECT MAX(purchase_month) FROM aggregated_royalties
        ))
        GROUP BY artist_id, artist_name, main_genre
        ORDER BY revenue DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    cur.close()
    if not row:
        raise HTTPException(status_code=404, detail="No artists found")
    return {"artist_id": row[0], "name": row[1], "genre": row[2], "revenue": float(row[3])}


@router.get("/api/revenue/trend6m")
def revenue_trend6m(db=Depends(get_db)):
    """Revenue ultimi 6 mesi."""
    logger.info("GET /api/revenue/trend6m")
    cur = db.cursor()
    cur.execute("""
        SELECT purchase_month, COALESCE(SUM(gross_rev), 0) AS revenue
        FROM aggregated_royalties
        WHERE purchase_month >= (
            SELECT DATE_TRUNC('month', MAX(purchase_month)) - INTERVAL '5 months'
            FROM aggregated_royalties
        )
        GROUP BY purchase_month
        ORDER BY purchase_month
    """)
    rows = cur.fetchall()
    cur.close()
    return {"trend": [{"month": r[0].strftime("%b %Y"), "revenue": float(r[1])} for r in rows]}


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
