import sqlite3
import os
from datetime import datetime
import os
print("[library] DB path:", os.path.abspath("library.db"))


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "library.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE,
            title TEXT,
            bpm REAL,
            duration REAL,
            waveform_path TEXT
        )
    """)
   
    conn.commit()
    conn.close()
    

    

def add_track(path, title, bpm, duration, waveform_path):
    path = os.path.normpath(os.path.abspath(path))
    """Insert a track into the library."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO tracks (path, title, bpm, duration, waveform_path)
        VALUES (?, ?, ?, ?, ?)
    """, (path, title, bpm, duration, waveform_path))

    conn.commit()
    conn.close()

def get_all_tracks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, path, title, bpm, duration, waveform_path
        FROM tracks
        ORDER BY title ASC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows

def get_track_by_id(track_id):
    """Return a single track by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
    row = cursor.fetchone()

    conn.close()
    return row

def delete_track_from_library(path):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tracks WHERE path = ?", (path,))

    conn.commit()
    conn.close()

    print(f"[library] Deleted track: {path}")
    
def track_exists_on_disk(path: str) -> bool:
    return os.path.exists(path)

def delete_invalid_paths():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tracks WHERE path LIKE '%.*'")
    conn.commit()
    conn.close()
