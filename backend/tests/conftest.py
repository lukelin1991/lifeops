"""
Test setup.

Tests run against a REAL Postgres database (not SQLite), because the app
uses Postgres features and types. By default that is:

    postgresql+psycopg://lifeops:lifeops@localhost:5432/lifeops_test

Override with TEST_DATABASE_URL. The database is dropped and recreated
at the start of the run and built with `alembic upgrade head`, so the
migrations themselves are tested too. Every test starts with empty tables.
"""

import os

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://lifeops:lifeops@localhost:5432/lifeops_test",
)

# These must be set BEFORE the app is imported (settings load at import).
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["AUTH_ENABLED"] = "false"
os.environ["TWELVE_DATA_API_KEY"] = ""
os.environ["COINGECKO_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

from app.main import app  # noqa: E402
from app.services.market_data import PriceResult, get_market_data  # noqa: E402
from tests.helpers import (  # noqa: E402
    create_database,
    drop_database,
    run_migrations,
)


@pytest.fixture(scope="session", autouse=True)
def test_database():
    create_database(TEST_DATABASE_URL)
    run_migrations(TEST_DATABASE_URL)
    yield
    from app.database import engine

    engine.dispose()
    drop_database(TEST_DATABASE_URL)


@pytest.fixture(autouse=True)
def clean_tables(test_database):
    """Empty every table after each test (ids restart at 1)."""
    yield
    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as connection:
        tables = connection.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename != 'alembic_version'"
            )
        ).scalars().all()
        if tables:
            connection.execute(
                text(
                    "TRUNCATE " + ", ".join(f'"{t}"' for t in tables)
                    + " RESTART IDENTITY CASCADE"
                )
            )
    engine.dispose()


class FakeMarketData:
    """
    Stand-in for MarketDataService: no network, prices you choose.
    Symbols without a price come back as "missing_api_key".
    """

    def __init__(self):
        self.prices: dict[tuple[str, str], object] = {}
        self.fail = False
        self.calls = 0

    def set_price(self, symbol, asset_type, price):
        from decimal import Decimal

        self.prices[(symbol, asset_type)] = Decimal(str(price))

    def get_prices(self, assets):
        self.calls += 1
        if self.fail:
            raise RuntimeError("market data exploded")

        results = {}
        for symbol, asset_type in assets:
            price = self.prices.get((symbol, asset_type))
            if price is None:
                results[(symbol, asset_type)] = PriceResult(
                    symbol, asset_type, None, "missing_api_key",
                    message="no key in tests",
                )
            else:
                results[(symbol, asset_type)] = PriceResult(
                    symbol, asset_type, price, "ok", "fake"
                )
        return results

    def get_price(self, symbol, asset_type):
        symbol = symbol.upper()
        return self.get_prices([(symbol, asset_type)])[(symbol, asset_type)]


@pytest.fixture
def market():
    fake = FakeMarketData()
    app.dependency_overrides[get_market_data] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_market_data, None)


@pytest.fixture
def client(market):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session():
    from app.database import SessionLocal

    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def auth_on(monkeypatch):
    """Turn single-user auth on for one test."""
    from app.config import settings

    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "app_username", "luke")
    monkeypatch.setattr(settings, "app_password", "correct horse")
    monkeypatch.setattr(settings, "app_password_hash", "")
    monkeypatch.setattr(settings, "jwt_secret", "test-secret-please-change-0123456789")
    monkeypatch.setattr(settings, "jwt_expire_minutes", 60)
    return settings
