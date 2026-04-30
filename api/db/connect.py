import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

USE_TURSO = os.environ.get("USE_TURSO", "false").lower() == "true"


class _TursoResult:
    def __init__(self, rows, columns):
        self._rows = rows
        self._columns = columns

    def fetchone(self):
        if not self._rows:
            return None
        return dict(zip(self._columns, self._rows[0]))

    def fetchall(self):
        return [dict(zip(self._columns, row)) for row in self._rows]


class _TursoConnection:
    def __init__(self, url, auth_token):
        import libsql_client
        self._client = libsql_client.create_client_sync(url=url, auth_token=auth_token)

    def execute(self, sql, params=()):
        import libsql_client
        result = self._client.execute(libsql_client.Statement(sql, list(params)))
        return _TursoResult(result.rows, result.columns)

    def commit(self):
        pass

    def close(self):
        self._client.close()


def get_db():
    if USE_TURSO:
        conn = _TursoConnection(
            url=os.environ["TURSO_URL"],
            auth_token=os.environ["TURSO_AUTH_TOKEN"],
        )
    else:
        import sqlite3
        conn = sqlite3.connect("webEng.db", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")

    try:
        yield conn
    finally:
        conn.close()
