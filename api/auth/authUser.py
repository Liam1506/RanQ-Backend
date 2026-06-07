from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from db.connect import db
from auth.authDb import auth_db, auth_db_admin

_bearer = HTTPBearer(auto_error=False)

def auth_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    return auth_db(db, credentials.credentials)

def auth_admin(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    return auth_db_admin(db, credentials.credentials)

def auth_user_with_role(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    user_id = credentials.credentials
    response = db.table("users").select("verified, admin").eq("id", user_id).execute()
    if not response.data:
        raise HTTPException(status_code=401, detail="Unauthorized")
    row = response.data[0]
    if not row["verified"]:
        raise HTTPException(status_code=402, detail="Unverified")
    return user_id, row["admin"]
