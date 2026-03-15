"""Data loading functions: read files and load into DB."""

import json
import csv
from datetime import date
from ..dataobjects import Artist, Work, Transaction
from .db_operations import (
    insert_artist,
    insert_work,
    insert_transaction,
    insert_quotas,
    get_artist_id,
    get_work_id,
)
from .logger import log_operation


def read_csv(filepath):
    """Read CSV file and return list of dictionaries."""
    csvdata = []
    try:
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                csvdata.append(row)
    except FileNotFoundError as e:
        print(f"Errore: Il file {filepath} non è stato trovato. {e}")
    except Exception as e:
        print(f"Errore durante la lettura del file: {e}")
    return csvdata


@log_operation
def load_artists(conn, loaded_at):
    """Load artists from artists.json into DB."""
    with open("data/artists.json", "r", encoding="utf-8") as f:
        artists_data = json.load(f)

    for a in artists_data['artists']:
        artist = Artist(
            name=a['artist_name'],
            royalty_pct=a['royalty_pct'],
            advance_paid=a['advanced_paid'],
            advance_pending=a['advance_pending'],
            is_front_artist=a['is_front_artist'],
            artist_image=a['artist_image'],
            main_genre=a['main_genre'],
            work_type=a['work_type'],
            loaded_at=loaded_at
        )
        db_id = insert_artist(conn, artist)
        print(f"✓ Artista inserito: {a['artist_name']} (ID: {db_id})")


@log_operation
def load_works(conn, loaded_at):
    """Load works from works.json into DB. Requires artists already in DB."""
    with open("data/artists.json", "r", encoding="utf-8") as f:
        artist_name_map = {i + 1: a['artist_name'] for i, a in enumerate(json.load(f)['artists'])}
    with open("data/works.json", "r", encoding="utf-8") as f:
        works_data = json.load(f)
    for w in works_data['works']:
        artist_name = artist_name_map[w['artist_id']]
        db_artist_id = get_artist_id(conn, artist_name)
        if not db_artist_id:
            print(f"  ⚠ Artista non trovato in DB: {artist_name}, salto {w['title']}.")
            continue
        work = Work(
            artist_id=db_artist_id,
            title=w['title'],
            secondary_artists_id=','.join(str(x) for x in w['secondary_artists_id']),
            work_cover=w['work_cover'],
            genre=w['genre'],
            bpm=w['bpm'],
            iswc=w['iswc'],
            song_key=w['key'],
            release_date=date.fromisoformat(w['release_date']),
            duration=w['duration_seconds'],
            loaded_at=loaded_at
        )
        work_id = insert_work(conn, work)
        print(f"  ✓ Opera inserita: {w['title']} (ID: {work_id})")


@log_operation
def load_transactions(conn, loaded_at, filepath="data/transaction.csv"):
    """Load transactions from CSV into DB. Requires works already in DB."""
    rows = read_csv(filepath)
    for row in rows:
        if not row.get('TITOLO'):
            continue
        work_id = get_work_id(conn, row['TITOLO'])
        if not work_id:
            print(f"  ⚠ Opera non trovata: {row['TITOLO']}, salto.")
            continue
        period = date.fromisoformat(row['MESE DI VENDITA'] + "-01")
        transaction = Transaction(
            work_id=work_id,
            period=period,
            gross_rev=float(row['GUADAGNI (USD)']),
            source=row['STORE'],
            platform_fee=None,
            distr_cost=None,
            is_artist_paid=False,
            purchase_month=row['MESE DI VENDITA'],
            platform=row['STORE'],
            territory=row['PAESE DI VENDITA'],
            streaming_source=row['TIPO DI RISORSA'],
            loaded_at=loaded_at
        )
        insert_transaction(conn, transaction)
        print(f"    ✓ Transazione: {row['STORE']} - {row['TITOLO']} ({row['GUADAGNI (USD)']}$)")


@log_operation
def load_quotas(conn, loaded_at):
    """Load royalty quotas (multi-artist splits) from works.json into DB."""
    with open("data/works.json", "r", encoding="utf-8") as f:
        works_data = json.load(f)
    for w in works_data['works']:
        work_id = get_work_id(conn, w['title'])
        if not work_id:
            print(f"  ⚠ Opera non trovata per quotas: {w['title']}, salto.")
            continue
        if w.get('quotas'):
            insert_quotas(conn, work_id, w['quotas'], loaded_at)
            print(f"  ✓ Quotas inserite per opera: {w['title']}")
