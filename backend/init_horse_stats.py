#!/usr/bin/env python3
"""Initialize horse_stats tables"""
import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Horse identities (unique by name+jockey+trainer)
cursor.execute("""
CREATE TABLE IF NOT EXISTS horse_identities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identity_key TEXT UNIQUE NOT NULL,
    horse_name TEXT NOT NULL,
    jockey TEXT,
    trainer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Individual race performances with results
cursor.execute("""
CREATE TABLE IF NOT EXISTS horse_performances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identity_key TEXT NOT NULL,
    race_date TEXT NOT NULL,
    hippodrome TEXT,
    distance INTEGER,
    odds REAL,
    position INTEGER,
    weather TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (identity_key) REFERENCES horse_identities(identity_key)
)
""")

# Aggregated horse stats (updated when results come in)
cursor.execute("""
CREATE TABLE IF NOT EXISTS horse_stats (
    identity_key TEXT PRIMARY KEY,
    total_races INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    podiums INTEGER DEFAULT 0,
    avg_position REAL DEFAULT 0,
    recent_form REAL DEFAULT 5.0,
    weather_stats TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (identity_key) REFERENCES horse_identities(identity_key)
)
""")

conn.commit()
conn.close()

print("✅ Tables created: horse_identities, horse_performances, horse_stats")
