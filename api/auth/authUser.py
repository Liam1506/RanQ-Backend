from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from db.connect import db
from auth.verifyUser import auth_user as _verify_auth_user

_bearer = HTTPBearer(auto_error=False)

def auth_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    return _verify_auth_user(db, credentials.credentials)