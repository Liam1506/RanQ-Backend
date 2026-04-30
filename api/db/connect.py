import sqlite3
import os

DB_PATH = "/tmp/webEng.db" if os.environ.get("VERCEL") else "webEng.db"

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
