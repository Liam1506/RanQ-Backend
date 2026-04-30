import uuid
from sqlite3 import Connection

def create_users_table(conn: Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id       TEXT    PRIMARY KEY,
            username TEXT    NOT NULL UNIQUE,
            email    TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            verified BOOl    NOT NULL,
            admin BOOl    NOT NULL
        )
        """
    )
    conn.commit()

def create_verify_table(conn: Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS verificationWaitlist (
            id       TEXT    NOT NULL,
            verifyId TEXT    PRIMARY KEY
        )
        """
    )
    conn.commit()


def get_user_by_username(conn: Connection, username: str):
    row = conn.execute(
        "SELECT id, username, email, password, verified, admin FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    return dict(row) if row else None

def get_user_by_email(conn: Connection, email: str):
    row = conn.execute(
        "SELECT id, username, email, password, verified, admin FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    return dict(row) if row else None

def insert_user(conn: Connection, username: str, email: str, hashed_password: str):
    create_verify_table(conn)
    user_id = str(uuid.uuid4())
    
    conn.execute(
        "INSERT INTO users (id, username, email, password, verified, admin) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, username, email, hashed_password, False, False),
    )

    conn.execute(
        "INSERT INTO verificationWaitlist (id, verifyId) VALUES (?, ?)",
        (user_id, str(uuid.uuid4())),
    )
    conn.commit()
    return user_id 



def verify_user(conn: Connection, userId: str, verifyId: str):
    create_verify_table(conn)

    row = conn.execute(
        "SELECT 1 FROM verificationWaitlist WHERE id = ? AND verifyId = ?",
        (userId, verifyId),
    ).fetchone()

    if row is None:
        return False

    conn.execute("UPDATE users SET verified = 1 WHERE id = ?", (userId,))
    conn.execute("DELETE FROM verificationWaitlist WHERE id = ?", (userId,))
    conn.commit()
    return True