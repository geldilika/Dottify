# import_csv.py  (minimal CSV -> DB)
import csv
from pathlib import Path
from decimal import Decimal
from dottify.models import Album, Song

BASE = Path("sample_data")

# --- Albums: expects columns: title,format,artist_name,release_date,retail_price
with open(BASE / "albums.csv", newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        if not row.get("title"):
            continue
        Album.objects.get_or_create(
            title=row["title"],
            defaults={
                "format": row.get("format", "ALBM"),
                "artist_name": row.get("artist_name", "Unknown"),
                "release_date": row.get("release_date", "2025-01-01"),
                "retail_price": Decimal(str(row.get("retail_price", "0.00"))),
            },
        )

# --- Songs: expects columns: title,album_title,length (seconds)
with open(BASE / "songs.csv", newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        if not row.get("title") or not row.get("album_title"):
            continue
        try:
            album = Album.objects.get(title=row["album_title"])
        except Album.DoesNotExist:
            continue
        length = int(row.get("length") or 180)  # fallback if missing
        Song.objects.get_or_create(
            title=row["title"],
            album=album,
            defaults={"length": length},
        )
