from operator import index
import json
import logging
import os

from fastapi import FastAPI, HTTPException, Query, Depends, UploadFile, File
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from pathlib import Path
from .db import connect_db
import shutil
import uuid

# API Logger
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("phobos.api")

# Transparent 1x1 PNG placeholder
PLACEHOLDER_PNG = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'


app = FastAPI(title="Phobos_api")

from .routes import router
app.include_router(router)

# Pydantic models
class Artist(BaseModel):
    artist_name: str
    royalty_pct: float
    advanced_paid: float = 0.0
    advance_pending: float = 0.0
    is_front_artist: bool = False
    artist_image: str = ""
    main_genre: str = ""
    work_type: str = "Album"

class Work(BaseModel):
    title: str
    artist_id: int
    secondary_artists_id: list = []
    quotas: list = []
    work_cover: str = ""
    release_date: str = ""
    iswc: str = ""
    genre: list = []
    duration_seconds: int = 0
    key: str = ""
    bpm: int = 0

# API Routes
@app.get("/api/artists")
def list_artists():
    """Get all artists"""
    logger.info("GET /api/artists")
    try:
        with open("data/artists.json", "r") as f:
            data = json.load(f)
            artists = data.get("artists", [])
            logger.info(f"Returning {len(artists)} artists")
            return {"artists": artists}
    except Exception as e:
        logger.error(f"GET /api/artists failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/artists")
def create_artist(artist: Artist):
    """Create a new artist"""
    logger.info(f"POST /api/artists - name={artist.artist_name}")
    try:
        with open("data/artists.json", "r") as f:
            data = json.load(f)

        new_artist = artist.model_dump()
        data["artists"].append(new_artist)

        with open("data/artists.json", "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Artist created: {artist.artist_name}")
        return {"status": "success", "artist": new_artist}
    except Exception as e:
        logger.error(f"POST /api/artists failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/works")
def list_works():
    """Get all works"""
    logger.info("GET /api/works")
    try:
        with open("data/works.json", "r") as f:
            data = json.load(f)
            works = data.get("works", [])
            logger.info(f"Returning {len(works)} works")
            return {"works": works}
    except Exception as e:
        logger.error(f"GET /api/works failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/works")
def create_work(work: Work):
    """Create a new work"""
    logger.info(f"POST /api/works - title={work.title}")
    try:
        with open("data/works.json", "r") as f:
            data = json.load(f)

        new_work = work.model_dump()
        data["works"].append(new_work)

        with open("data/works.json", "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Work created: {work.title}")
        return {"status": "success", "work": new_work}
    except Exception as e:
        logger.error(f"POST /api/works failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_db():
    conn = connect_db()
    try: 
        yield conn
    finally: 
        conn.close()


@app.get("/health")
def health():
    logger.info("GET /health")
    return {"status" : "OK", "version":"0.0.1"}

@app.get("/artist/{artist_id}")
def get_artist(artist_id: str):
    logger.info(f"GET /artist/{artist_id}")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM artists WHERE artist_id = %s", (artist_id))
    artist = cur.fetchone()
    cur.close()
    if not artist:
        logger.warning(f"Artist {artist_id} not found")
        raise HTTPException(404, "artist not found")
    return {"artist_id" : artist_id, "name" : artist[0]}


@app.get("/revenue")
def get_revenue(artist_id: int = Query(..., ge=1),
                year: int = Query(2025, ge=2020),
                db = Depends(get_db)):
    logger.info(f"GET /revenue - artist_id={artist_id} year={year}")
    cur = db.cursor()
    cur.execute("""SELECT COALESCE (SUM(t.gross_rev), 0)
                FROM transactions t
                JOIN works w ON w.work_id = t.work_id
                WHERE w.artist_id = %s AND EXTRACT(YEAR FROM t.period) = %s""",(artist_id, year))
    total = cur.fetchone()[0] or 0
    cur.close()
    logger.info(f"Revenue for artist {artist_id} year {year}: {total}")
    return {"artist_id":artist_id, "year":year, "total_revenue":total}

@app.get("/api/revenue/by-artist")
def get_revenue_by_artist(db = Depends(get_db)):
    """Get total revenue for each artist"""
    logger.info("GET /api/revenue/by-artist")
    cur = db.cursor()
    cur.execute("""
        SELECT a.artist_id, a.name, COALESCE(SUM(t.gross_rev), 0) as total_revenue
        FROM artists a
        LEFT JOIN works w ON a.artist_id = w.artist_id
        LEFT JOIN transactions t ON w.work_id = t.work_id
        GROUP BY a.artist_id, a.name
        ORDER BY total_revenue DESC
    """)
    results = cur.fetchall()
    cur.close()
    logger.info(f"Returning revenue for {len(results)} artists")
    return {
        "revenues": [
            {"artist_id": r[0], "artist_name": r[1], "total_revenue": float(r[2])}
            for r in results
        ]
    }

@app.get("/api/revenue/by-artist-month")
def get_revenue_by_artist_month(db = Depends(get_db)):
    """Get revenue for each artist per month"""
    logger.info("GET /api/revenue/by-artist-month")
    cur = db.cursor()
    cur.execute("""
        SELECT a.artist_id, a.name, t.purchase_month, COALESCE(SUM(t.gross_rev), 0) as monthly_revenue
        FROM artists a
        LEFT JOIN works w ON a.artist_id = w.artist_id
        LEFT JOIN transactions t ON w.work_id = t.work_id
        WHERE t.purchase_month IS NOT NULL
        GROUP BY a.artist_id, a.name, t.purchase_month
        ORDER BY a.artist_id, t.purchase_month
    """)
    results = cur.fetchall()
    cur.close()
    logger.info(f"Returning {len(results)} monthly revenue records")
    return {
        "revenues": [
            {"artist_id": r[0], "artist_name": r[1], "month": r[2], "revenue": float(r[3])}
            for r in results
        ]
    }

@app.get("/")
def root():
    return FileResponse("frontend/index.html")

@app.get("/artists")
def artists():
    return FileResponse("frontend/artists.html")

@app.get("/works")
def works():
    return FileResponse("frontend/works.html")

@app.get("/assets/phobos_logo.png")
def logo():
    return FileResponse("frontend/phobos_logo.png")

@app.get("/assets/shared.css")
def shared_css():
    return FileResponse("frontend/shared.css", media_type="text/css")

@app.get("/assets/shared.js")
def shared_js():
    return FileResponse("frontend/shared.js", media_type="application/javascript")

@app.get("/assets/artists/{filename}")
def get_artist_image(filename: str):
    image_path = Path(__file__).parent.parent / "frontend" / "src" / "artists" / filename
    if not image_path.exists():
        return Response(status_code=204)
    return FileResponse(str(image_path))

@app.get("/assets/albums/{filename}")
def get_album_image(filename: str):
    image_path = Path(__file__).parent.parent / "frontend" / "src" / "albums" / filename
    if not image_path.exists():
        return Response(status_code=204)
    return FileResponse(str(image_path))

@app.post("/api/upload/artist-image")
async def upload_artist_image(file: UploadFile = File(...)):
    logger.info(f"POST /api/upload/artist-image - file={file.filename}")
    file_ext = file.filename.rsplit('.', 1)[-1].lower()
    file_name = f"artist_{uuid.uuid4().hex[:8]}.{file_ext}"
    file_path = Path(__file__).parent.parent / "frontend" / "src" / "artists" / file_name
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    logger.info(f"Artist image saved: {file_name}")
    return {"filename": file_name}

@app.post("/api/upload/work-cover")
async def upload_work_cover(file: UploadFile = File(...)):
    logger.info(f"POST /api/upload/work-cover - file={file.filename}")
    file_ext = file.filename.rsplit('.', 1)[-1].lower()
    file_name = f"cover_{uuid.uuid4().hex[:8]}.{file_ext}"
    file_path = Path(__file__).parent.parent / "frontend" / "src" / "albums" / file_name
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    logger.info(f"Work cover saved: {file_name}")
    return {"filename": file_name}



# Run with:
"""
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
"""