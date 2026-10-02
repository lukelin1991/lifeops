"""
Application settings.

Everything that changes between environments (laptop, CI, AWS) is read
from environment variables. For local development, values can live in
backend/.env, which python-dotenv loads automatically.
"""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

# Load backend/.env if it exists. Real environment variables win.
load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)

    if value is None or value.strip() == "":
        return default

    return value.strip().lower() in ("1", "true", "yes", "on")


def _get_int(name: str, default: int) -> int:
    value = os.environ.get(name)

    if value is None or value.strip() == "":
        return default

    return int(value)


def _get_list(name: str, default: str) -> list[str]:
    value = os.environ.get(name, default)

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


@dataclass
class Settings:
    # Database
    database_url: str = field(
        default_factory=lambda: os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://lifeops:lifeops@localhost:5432/lifeops",
        )
    )

    # CORS: comma-separated list of allowed frontend origins
    cors_origins: list[str] = field(
        default_factory=lambda: _get_list(
            "CORS_ORIGINS",
            "http://localhost:5173",
        )
    )

    # Used to decide what "today" means for agendas and summaries
    timezone: str = field(
        default_factory=lambda: os.environ.get(
            "APP_TIMEZONE",
            "America/New_York",
        )
    )

    # Auth (single user)
    auth_enabled: bool = field(
        default_factory=lambda: _get_bool("AUTH_ENABLED", False)
    )
    app_username: str = field(
        default_factory=lambda: os.environ.get("APP_USERNAME", "luke")
    )
    app_password_hash: str = field(
        default_factory=lambda: os.environ.get("APP_PASSWORD_HASH", "")
    )
    app_password: str = field(
        default_factory=lambda: os.environ.get("APP_PASSWORD", "")
    )
    jwt_secret: str = field(
        default_factory=lambda: os.environ.get("JWT_SECRET", "")
    )
    jwt_expire_minutes: int = field(
        default_factory=lambda: _get_int("JWT_EXPIRE_MINUTES", 720)
    )

    # Market data
    twelve_data_api_key: str = field(
        default_factory=lambda: os.environ.get("TWELVE_DATA_API_KEY", "")
    )
    coingecko_api_key: str = field(
        default_factory=lambda: os.environ.get("COINGECKO_API_KEY", "")
    )
    market_cache_ttl_seconds: int = field(
        default_factory=lambda: _get_int("MARKET_CACHE_TTL_SECONDS", 60)
    )
    market_http_timeout_seconds: int = field(
        default_factory=lambda: _get_int("MARKET_HTTP_TIMEOUT_SECONDS", 8)
    )


# One shared settings object for the whole app.
settings = Settings()
