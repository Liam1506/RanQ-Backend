import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

USE_TURSO = os.environ.get("USE_TURSO", "false").lower() == "true"

def get_db():
    if USE_TURSO:
        import libsql_experimental as libsql
        conn = libsql.connect(
            os.environ["TURSO_URL"],
            auth_token=os.environ["TURSO_AUTH_TOKEN"],
        )
    else:
        import sqlite3
        db_path = "/tmp/webEng.db" if os.environ.get("VERCEL") else "webEng.db"
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")

    try:
        yield conn
    finally:
        conn.close()
