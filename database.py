"""
Database connection module
- Local: SQLite (database.db)
- Production: PostgreSQL via Supabase (set DATABASE_URL env variable)
"""
import os
import sqlite3
import psycopg2
import psycopg2.extras
from urllib.parse import quote_plus

_password = quote_plus('payal6269Nika@10965')
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    f'postgresql://postgres.tdapvcfpihkskolkiiyy:{_password}@aws-0-ap-south-1.pooler.supabase.com:5432/postgres'
)

# Detect mode
USE_SQLITE = not bool(os.environ.get('DATABASE_URL'))


# ── SQLite wrapper to mimic psycopg2 RealDictCursor ──────────────────────────

class SQLiteRow(dict):
    pass

class SQLiteCursor:
    def __init__(self, cursor):
        self._cur = cursor
        self.lastrowid = None

    def execute(self, sql, params=()):
        # Convert %s → ? for SQLite
        sql = sql.replace('%s', '?')
        # Convert SERIAL PRIMARY KEY → INTEGER PRIMARY KEY AUTOINCREMENT
        sql = sql.replace('SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
        # Convert ILIKE → LIKE for SQLite
        sql = sql.replace('ILIKE', 'LIKE')
        # Remove RETURNING id (SQLite doesn't support it)
        returning = False
        if 'RETURNING id' in sql:
            sql = sql.replace('RETURNING id', '')
            returning = True
        self._cur.execute(sql, params)
        self.lastrowid = self._cur.lastrowid
        self._returning = returning

    def fetchone(self):
        if self._returning:
            return {'id': self.lastrowid}
        row = self._cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in self._cur.description]
        return SQLiteRow(zip(cols, row))

    def fetchall(self):
        rows = self._cur.fetchall()
        if not rows:
            return []
        cols = [d[0] for d in self._cur.description]
        return [SQLiteRow(zip(cols, r)) for r in rows]

    def close(self):
        self._cur.close()

    @property
    def description(self):
        return self._cur.description


class SQLiteConnection:
    def __init__(self, path):
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self.autocommit = False

    def cursor(self, cursor_factory=None):
        return SQLiteCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


# ── Public API ────────────────────────────────────────────────────────────────

def get_db_connection():
    if USE_SQLITE:
        return SQLiteConnection('database.db')
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    return conn


def dict_cursor(conn):
    if USE_SQLITE:
        return conn.cursor()
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        roll_no TEXT UNIQUE NOT NULL,
        role TEXT DEFAULT 'user'
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS items(
        id SERIAL PRIMARY KEY,
        name TEXT, description TEXT, category TEXT,
        type TEXT, image_data TEXT,
        reported_by TEXT, phone TEXT, email TEXT,
        reported_at TEXT, status TEXT DEFAULT 'active',
        location TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS messages(
        id SERIAL PRIMARY KEY,
        item_id INTEGER,
        sender TEXT, receiver TEXT,
        message TEXT, sent_at TEXT,
        is_read INTEGER DEFAULT 0
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS claim_requests(
        id SERIAL PRIMARY KEY,
        item_id INTEGER, item_name TEXT,
        requested_by TEXT, user_phone TEXT,
        user_email TEXT, message TEXT,
        requested_at TEXT, status TEXT DEFAULT 'pending'
    )""")

    conn.commit()
    cur.close()
    conn.close()
    mode = 'SQLite (local)' if USE_SQLITE else 'Supabase PostgreSQL'
    print(f"Database initialized on {mode}.")


if __name__ == '__main__':
    init_db()
