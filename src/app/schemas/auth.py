from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=3)
    password: str = Field(min_length=8)
    role: str = Field(default="perawat")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
