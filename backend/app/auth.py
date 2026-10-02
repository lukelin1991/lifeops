"""
Single-user authentication.

There is exactly one user (Luke), configured with environment variables:

    AUTH_ENABLED=true
    APP_USERNAME=luke
    APP_PASSWORD_HASH='$2b$12$...'   # bcrypt hash (preferred)
    APP_PASSWORD=...                 # plain text, local dev only
    JWT_SECRET=<long random string>

POST /auth/login checks the password and returns a signed JWT. Every
protected route depends on `require_auth`, which validates the
"Authorization: Bearer <token>" header. With AUTH_ENABLED=false (the
default for local development) `require_auth` lets every request in.
"""

import datetime
import hmac

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

JWT_ALGORITHM = "HS256"

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str) -> bool:
    if settings.app_password_hash:
        try:
            return bcrypt.checkpw(
                password.encode(),
                settings.app_password_hash.encode(),
            )
        except ValueError:
            # Malformed hash, or password longer than bcrypt's 72 bytes
            return False

    if settings.app_password:
        return hmac.compare_digest(
            password.encode(),
            settings.app_password.encode(),
        )

    return False


def check_auth_config() -> None:
    """Fail fast if auth is on but can't possibly work."""
    if not settings.auth_enabled:
        return

    if not settings.jwt_secret:
        raise RuntimeError("AUTH_ENABLED=true requires JWT_SECRET")

    if not (settings.app_password_hash or settings.app_password):
        raise RuntimeError(
            "AUTH_ENABLED=true requires APP_PASSWORD_HASH or APP_PASSWORD"
        )


def create_access_token(username: str) -> tuple[str, int]:
    expires_in = settings.jwt_expire_minutes * 60
    now = datetime.datetime.now(datetime.UTC)

    payload = {
        "sub": username,
        "iat": now,
        "exp": now + datetime.timedelta(seconds=expires_in),
    }

    token = jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)
    return token, expires_in


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str | None:
    """Dependency for protected routes. Returns the username."""
    if not settings.auth_enabled:
        return None

    if credentials is None:
        raise _unauthorized("Not authenticated")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Session expired, please log in again")
    except jwt.InvalidTokenError:
        raise _unauthorized("Invalid token")

    if payload.get("sub") != settings.app_username:
        raise _unauthorized("Invalid token")

    return payload["sub"]
