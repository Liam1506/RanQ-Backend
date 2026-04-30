from sqlite3 import Connection
from fastapi import HTTPException

def auth_user(conn: Connection, id: str):
    row = conn.execute(
        "SELECT verified, admin FROM users WHERE id = ?",
        (id,),
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if dict(row)["verified"] == False:
         raise HTTPException(status_code=402, detail="Unverified")
    return True