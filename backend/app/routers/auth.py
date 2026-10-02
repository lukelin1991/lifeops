from fastapi import APIRouter, Depends, HTTPException

from app.auth import create_access_token, require_auth, verify_password
from app.config import settings
from app.schemas.auth import AuthConfig, LoginRequest, TokenResponse

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.get("/config", response_model=AuthConfig)
def auth_config():
    """Public: tells the frontend whether it needs to show a login page."""
    return {"auth_enabled": settings.auth_enabled}


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest):
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=400,
            detail="Authentication is disabled (AUTH_ENABLED=false)"
        )

    if not settings.jwt_secret:
        raise HTTPException(
            status_code=500,
            detail="Server misconfigured: JWT_SECRET is not set"
        )

    username_ok = credentials.username == settings.app_username
    password_ok = verify_password(credentials.password)

    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    token, expires_in = create_access_token(settings.app_username)
    return {"access_token": token, "expires_in": expires_in}


@router.get("/me")
def me(username: str | None = Depends(require_auth)):
    return {
        "username": username or settings.app_username,
        "auth_enabled": settings.auth_enabled,
    }
