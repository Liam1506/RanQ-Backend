from sqlite3 import Connection


def create_users_table(conn: Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE,
            email    TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL
        )
        """
    )
    conn.commit()


def get_user_by_username(conn: Connection, username: str):
    row = conn.execute(
        "SELECT id, username, email, password FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    return dict(row) if row else None


def get_user_by_email(conn: Connection, email: str):
    row = conn.execute(
        "SELECT id, username, email, password FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    return dict(row) if row else None


def insert_user(conn: Connection, username: str, email: str, hashed_password: str):
    conn.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (username, email, hashed_password),
    )
    conn.commit()
