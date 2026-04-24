import sqlite3
import json
import os
import uuid
import time

DB_PATH = os.environ.get("DB_PATH", "profiles.db")
SEED_PATH = os.environ.get("SEED_PATH", "seed_profiles.json")


def uuid7() -> str:
    """Generate a UUID v7 (time-ordered)."""
    timestamp_ms = int(time.time() * 1000)
    time_high = (timestamp_ms >> 16) & 0xFFFFFFFF
    time_low = timestamp_ms & 0xFFFF
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF
    rand_b = int.from_bytes(os.urandom(8), "big") & 0x3FFFFFFFFFFFFFFF

    # Build 128-bit UUID v7
    hi = (time_high << 32) | (time_low << 16) | (0x7000 | rand_a)
    lo = (0x8000000000000000 | rand_b)

    combined = (hi << 64) | lo
    hex_str = f"{combined:032x}"
    return f"{hex_str[0:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            gender TEXT NOT NULL,
            gender_probability REAL NOT NULL,
            age INTEGER NOT NULL,
            age_group TEXT NOT NULL,
            country_id TEXT NOT NULL,
            country_name TEXT NOT NULL,
            country_probability REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_gender ON profiles(gender)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_age_group ON profiles(age_group)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_country_id ON profiles(country_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_age ON profiles(age)")
    conn.commit()

    # Seed if not already seeded
    count = cur.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
    if count == 0:
        _seed(conn, cur)

    conn.close()


def _seed(conn, cur):
    if not os.path.exists(SEED_PATH):
        print(f"Seed file not found: {SEED_PATH}")
        return

    with open(SEED_PATH, "r") as f:
        data = json.load(f)

    profiles = data.get("profiles", [])
    inserted = 0

    for p in profiles:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO profiles
                    (id, name, gender, gender_probability, age, age_group,
                     country_id, country_name, country_probability, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
            """, (
                uuid7(),
                p["name"],
                p["gender"],
                p["gender_probability"],
                p["age"],
                p["age_group"],
                p["country_id"],
                p["country_name"],
                p["country_probability"],
            ))
            inserted += 1
        except Exception as e:
            print(f"Skipping {p.get('name')}: {e}")

    conn.commit()
    print(f"Seeded {inserted} profiles.")
