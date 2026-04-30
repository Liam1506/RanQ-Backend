from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class VerifyList(BaseModel):
    id: str
    verId: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    verified: bool
    admin: bool
