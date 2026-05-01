from fastapi import APIRouter, Depends, HTTPException, status
import bcrypt

from db.connect import get_db
from auth.db import get_user_by_username, get_user_by_email, insert_user, verify_user
from auth.schemas import RegisterRequest, LoginRequest, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db=Depends(get_db)):
    if get_user_by_username(db, body.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    if get_user_by_email(db, body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(body.password)
    insert_user(db, body.username, body.email, hashed)

    user = get_user_by_username(db, body.username)
    return user


@router.post("/login")
def login(body: LoginRequest, db=Depends(get_db)):
    user = get_user_by_username(db, body.username)
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return {"message": "Login successful", "user": {"id": user["id"], "username": user["username"], "email": user["email"]}}


@router.get("/verify")
def verify(userId: str, verifyId: str, db=Depends(get_db)):
    if not verify_user(db, userId, verifyId):
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")
    return {"message": "Account verified successfully"}
