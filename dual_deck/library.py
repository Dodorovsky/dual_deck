import sqlite3
import os
from datetime import datetime

DB_PATH = "library.db"

def init_db():
    """Create the database and tracks table if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE,
            title TEXT,
            bpm REAL,
            duration REAL,
            waveform_path TEXT,
            date_added TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_track(path, title, bpm, duration, waveform_path):
    """Insert a track into the library."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO tracks (path, title, bpm, duration, waveform_path, date_added)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (path, title, bpm, duration, waveform_path, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_all_tracks():
    """Return all tracks in the library."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, bpm, duration, path FROM tracks ORDER BY title ASC")
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
