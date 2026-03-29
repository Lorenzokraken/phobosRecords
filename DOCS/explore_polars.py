import polars as pl

# Carica i dati
df_works = pl.read_json("data/works.json")
df_artists_raw = pl.read_json("data/artists.json")
df_transactions = pl.read_csv("data/transaction.csv")

# Espandi la colonna 'artists' in righe
df_artists = df_artists_raw.explode("artists").unnest("artists")

# Rinomina colonne per uniformità
df_transactions = df_transactions.rename({
    "ARTISTA": "artist_name",
    "TITOLO": "title"
})

# Espandi df_works aggiungendo artist_name (tramite join con artist_id)
# Prima crea una mappatura artist_id → artist_name
df_artists_lookup = df_artists.select(["artist_name", "artist_id"])

# Unisci works con artist_name
df_works_expanded = df_works.join(df_artists_lookup, on="artist_id", how="left")

# Ora unisci tutto
df_full = df_transactions.join(df_works_expanded, on=["artist_name", "title"], how="left")

print(df_full)