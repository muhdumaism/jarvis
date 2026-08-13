"""
JARVIS — Authentication API Router
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import timedelta

from app.core.config import settings
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_in: int
    role: str


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    """Authenticate credentials and return JWT token."""
    # Check default credential fallback (configured via .env)
    if data.username == settings.default_admin_username and data.password == settings.default_admin_password:
        access_token = create_access_token(
            data={"sub": data.username, "role": "admin"}
        )
        return LoginResponse(
            token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
            role="admin"
        )
    
    # Custom users authentication logic can go here (DB queries), but
    # in the context of this smart home server, the default admin is the primary user.
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
