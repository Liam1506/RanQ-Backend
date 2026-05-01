from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from db.connect import db
from auth.authDb import auth_db 

_bearer = HTTPBearer(auto_error=False)

def auth_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    return auth_db(db, credentials.credentials)